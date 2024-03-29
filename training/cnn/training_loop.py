import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import StepLR

from torch.utils.data import DataLoader
import torchvision.datasets as datasets
import torchvision.transforms as transforms

from .train import train, test
from lib.networks.classifier import Net


def training_loop(batch_size, epochs, gamma, seed, log_interval, save_model):
    torch.manual_seed(seed)

    use_cuda = True if torch.cuda.is_available() else False
    if use_cuda: # TODO: add cuda checks across all code
        torch.cuda.set_device(0)
        print('CUDA support is enabled')

    ngpu = torch.cuda.device_count()
    device = torch.device("cuda:0" if (use_cuda and ngpu > 0) else "cpu")

    transform=transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5), (0.5))
    ])

    trainset = datasets.MNIST("./data/mnist", train=True, download=True, transform=transform)
    train_loader = DataLoader(trainset, batch_size=batch_size, shuffle=True)

    testset = datasets.MNIST("./data/mnist", train=False, download=True, transform=transform)
    test_loader = DataLoader(testset, batch_size=batch_size, shuffle=True)

    model = Net(ngpu).to(device)
    loss = nn.NLLLoss() # This criterion combines nn.LogSoftmax() and nn.NLLLoss() in one single class.

    if use_cuda:
        model = nn.DataParallel(model, list(range(ngpu)))
        loss.cuda()

    # optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    # optimizer = optim.Adadelta(model.parameters(), lr=args.lr)
    optimizer = optim.Adam(model.parameters())

    scheduler = StepLR(optimizer, step_size=1, gamma=gamma)
    for epoch in range(1, epochs + 1):
        train(model, device, train_loader, loss, optimizer, epoch, log_interval)
        test(model, device, loss, test_loader)
        scheduler.step()

    if save_model:
        torch.save(model.state_dict(), "../classifier.pt")
