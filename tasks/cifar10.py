import torchvision
import torch.utils.data as torch_data
from torchvision.transforms import transforms

from models.resnet import resnet18
from tasks.task import Task


class Cifar10Task(Task):

    def load_data(self):
        if self.params.transform_train:
            transform_train = transforms.Compose([
                transforms.RandomCrop(32, padding=4),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize((0.4914, 0.4822, 0.4465),
                                     (0.2023, 0.1994, 0.2010)),
            ])
        else:
            transform_train = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize((0.4914, 0.4822, 0.4465),
                                     (0.2023, 0.1994, 0.2010)),
            ])
        transform_test = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465),
                                 (0.2023, 0.1994, 0.2010)),
        ])
        self.train_dataset = torchvision.datasets.CIFAR10(root='./data',
                                                          train=True,
                                                          download=True,
                                                          transform=transform_train)
        if self.params.poison_images:
            self.train_loader = self.remove_semantic_backdoors()
        else:
            self.train_loader = torch_data.DataLoader(self.train_dataset,
                                                      batch_size=self.params.batch_size,
                                                      shuffle=True,
                                                      num_workers=2)
        self.test_dataset = torchvision.datasets.CIFAR10(root='./data',
                                                         train=False,
                                                         download=True,
                                                         transform=transform_test)
        self.test_loader = torch_data.DataLoader(self.test_dataset,
                                                 batch_size=self.params.test_batch_size,
                                                 shuffle=False, num_workers=2)

        self.classes = ('plane', 'car', 'bird', 'cat',
                        'deer', 'dog', 'frog', 'horse', 'ship', 'truck')
        return True

    def build_model(self) -> None:
        self.model = resnet18(pretrained=self.params.pretrained,
                              num_classes=len(self.classes))

    def remove_semantic_backdoors(self):
        """
        Semantic backdoors still occur with unmodified labels in the training
        set. This method removes them, so the only occurrence of the semantic
        backdoor will be in the
        :return: None
        """

        all_images = set(range(len(self.train_dataset)))
        unpoisoned_images = list(all_images.difference(set(
            self.params.poison_images)))

        self.train_loader = torch_data.DataLoader(self.train_dataset,
                                     batch_size=self.params.batch_size,
                                     sampler=torch_data.sampler.SubsetRandomSampler(
                                         unpoisoned_images))