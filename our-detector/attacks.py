import torch
import torchvision
import torch.nn.functional as F
from torchvision import transforms
from torchvision.utils import save_image
from torch.utils.data import DataLoader
from advertorch.attacks import LinfPGDAttack, PGDAttack, GradientSignAttack
from tqdm import tqdm

from model import DetectorNet
from utils import *

def PGD_attack(X, y, model, loss_fn, eps=0.15, eps_iter=0.1):
    adversary = PGDAttack(
        model, loss_fn=loss_fn, eps=eps,
        nb_iter=1, eps_iter=eps_iter, rand_init=True, clip_min=0.0, clip_max=1.0,
        targeted=False)

    X = adversary.perturb(X, y)

    return X, y

def LinfPGD_Attack(X, y, model, loss_fn, eps=0.15, eps_iter=0.1):
    adversary = LinfPGDAttack(
        model, loss_fn=loss_fn, eps=eps,
        nb_iter=1, eps_iter=eps_iter, rand_init=True, clip_min=0.0, clip_max=1.0,
        targeted=False)

    X = adversary.perturb(X, y)

    return X, y

def FGSM_attack(X, y, model, loss_fn, eps=0.15, eps_iter=0.1):
    adversary = GradientSignAttack(model, loss_fn=loss_fn, eps=eps, targeted=False)

    X = adversary.perturb(X, y)

    return X, y

def generateAdverserials(model, data_loader, output_dir, attack_type='PGD', device='cpu'):
    """Generates Adverserials (for a given model and attack), then saves them to the output folder.

    Args:
        model (nn.Module): The Pytorch model on which we do the adverserial attack
        data_loader (torch.utils.data.dataloader.DataLoader): Data loader for the input data
        output_dir (str): Path to your output folder. Place to save the generated adverserials.
        attack_type (str): Which attack you want to run on the model
                        Default: 'PGD'
        device (torch.device): To run your model on the gpu ('cuda') or cpu ('cpu')
                        Default: 'cpu'
    """

    # Set the model in Evaluation mode!
    model.eval()
    imageCount = 0

    # Loop through the given data_loader and create the adverserial images
    with tqdm(data_loader) as tepoch:
        for batch_idx, (data, true_label) in enumerate(tepoch):
            # Move to device and correct dimensions
            data, true_label = data.to(device), true_label.to(device)
            true_label = torch.unsqueeze(true_label.to(torch.float32), dim=1)

            # Make the attack
            if attack_type == 'LinfPGD':
                adv_untargeted = LinfPGD_Attack(data, true_label, model, F.binary_cross_entropy)
            elif attack_type == 'PGD':
                adv_untargeted = PGD_attack(data, true_label, model, F.binary_cross_entropy)
            elif attack_type == 'FGSM':
                adv_untargeted = FGSM_attack(data, true_label, model, F.binary_cross_entropy)
            else:
                raise NotImplementedError("This type of attack has not been implemented yet")

            # Save images
            for i in range(adv_untargeted[0].shape[0]):
                if imageCount > 99999:
                    raise ResourceWarning("You exeed the number of adverserials of 10000")
                
                if adv_untargeted[1][i] == 0:
                    save_image(adv_untargeted[0][i], f'{output_dir}/fake/{imageCount:05}.png')
                    imageCount += 1
                elif adv_untargeted[1][i] == 1:
                    save_image(adv_untargeted[0][i], f'{output_dir}/real/{imageCount:05}.png')
                    imageCount += 1
                else:
                    raise ValueError(f"Expected label value of 0 or 1. But received {adv_untargeted[1][i]}")


# Get the Model
# TODO: Move this to a separate File
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DetectorNet().to(device)
model.load_state_dict(torch.load('checkpoints/checkpoint.pt'))


# Create Dataloader
# TODO: Have a separate File for Data Loaders
BATCH_SIZE = 10

user = "Nici"
if user=="Mo":
    data_dir_test = "/home/moritz/Documents/ETH/DL/Data/test"
if user=="Nici":
    data_dir_test="/home/nicolas/git/robust-deepfake-detector/our-detector/data/test"

transform = transforms.Compose([
    transforms.ToTensor()
    # Maybe Normalize !!!!
])

# 0: Fake, 1: Real
test_data = torchvision.datasets.ImageFolder(root=data_dir_test,transform = transform)
test_data_loader = DataLoader(test_data, batch_size=BATCH_SIZE, shuffle=True)


# Generate the Adverserials
# TODO: Call this from a separate File
generateAdverserials(
    model = model, 
    data_loader = test_data_loader, 
    output_dir = "data/adverserials",
    attack_type='LinfPGD',
    device = device
)
