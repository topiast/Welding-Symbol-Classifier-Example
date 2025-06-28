import torch
import random
from torchvision.transforms import functional as F
from PIL import Image
import numpy as np

def sample_normal(mu, sigma, min_val, max_val):
    """Samples from a normal distribution, clamping the value within a specified range."""
    return np.clip(random.normalvariate(mu, sigma), min_val, max_val)

def apply_augmentation(image, aug_type):
    """Applies a single, randomly configured augmentation to an image."""
    if aug_type == 'scale_zoom':
        # UI range: 0.1x to 3.0x. Mu=1.0 (no zoom). Sigma chosen to allow for reasonable zooming.
        scale_factor = sample_normal(mu=0.8, sigma=0.3, min_val=0.2, max_val=1.4)
        
        original_width, original_height = image.size
        
        if scale_factor > 1.0:
            # Zoom In: Crop the center and resize
            s_width = int(original_width / scale_factor)
            s_height = int(original_height / scale_factor)
            s_x = (original_width - s_width) // 2
            s_y = (original_height - s_height) // 2
            
            cropped_image = F.crop(image, s_y, s_x, s_height, s_width)
            return F.resize(cropped_image, [original_height, original_width])
        
        elif scale_factor < 1.0:
            # Zoom Out: Resize the image and paste it onto a new canvas
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            if new_width <= 0 or new_height <= 0: return image

            resized_image = F.resize(image, [new_height, new_width])
            
            # Create a new image with a white background
            new_image = Image.new("RGB", (original_width, original_height), (255, 255, 255))
            
            # Paste the resized image into the center
            paste_x = (original_width - new_width) // 2
            paste_y = (original_height - new_height) // 2
            new_image.paste(resized_image, (paste_x, paste_y))
            
            return new_image
    elif aug_type == 'brightness':
        # UI range: 0% to 200%. Mu=1.0 (100%). Sigma chosen for reasonable variation.
        brightness_factor = sample_normal(mu=1.0, sigma=0.3, min_val=0.0, max_val=2.0)
        return F.adjust_brightness(image, brightness_factor)
    elif aug_type == 'contrast':
        # UI range: 0% to 200%. Mu=1.0 (100%).
        contrast_factor = sample_normal(mu=1.0, sigma=0.3, min_val=0.0, max_val=2.0)
        return F.adjust_contrast(image, contrast_factor)
    elif aug_type == 'noise':
        # UI range: 0 to 100. Corresponds to noise_intensity 0.0 to 1.0. Mu=0.
        noise_intensity = sample_normal(mu=0.0, sigma=0.2, min_val=0.0, max_val=1.0)
        if noise_intensity > 0:
            image_np = np.array(image.convert('RGB')).astype(np.float32)
            # Scale noise effect to be more pronounced, similar to UI's `* 2.55`
            noise = (np.random.randn(*image_np.shape) * (noise_intensity * 100))
            noisy_image_np = np.clip(image_np + noise, 0, 255).astype(np.uint8)
            return Image.fromarray(noisy_image_np)
    return image


def generate_augmented_samples(original_dataset, augmentation_counts=None):
    """
    Generates an augmented dataset from an original dataset.

    This function takes a dataset of PIL images, creates augmented versions
    in memory, and returns a list of (PIL image, label) tuples.

    Args:
        original_dataset: A PyTorch Dataset object that returns (PIL_Image, label).
        augmentation_counts (dict, optional): Specifies how many augmentations of each
                                             type to create. Defaults to 250 per type.

    Returns:
        list: A list of (PIL.Image.Image, int) tuples representing the
              original and augmented samples.
    """
    if augmentation_counts is None:
        augmentation_counts = {
            'scale_zoom': 400,
            'brightness': 400,
            'contrast': 400,
            'noise': 400,
            'multi': 800,
        }

    # Start with the original samples
    augmented_samples = [sample for sample in original_dataset]

    if not original_dataset:
        return []

    print(f"Starting with {len(original_dataset)} original samples.")
    print(f"Generating augmentations based on counts: {augmentation_counts}")

    # Generate augmented images
    for aug_type, count in augmentation_counts.items():
        for _ in range(count):
            # Get a random image and its label from the original dataset
            image, label = random.choice(original_dataset)
            
            augmented_image = image
            if aug_type == 'multi':
                # Apply a random number of different augmentations
                available_augs = [k for k in augmentation_counts.keys() if k != 'multi']
                num_to_apply = random.randint(2, len(available_augs))
                augs_to_apply = random.sample(available_augs, num_to_apply)
                
                for multi_aug in augs_to_apply:
                    augmented_image = apply_augmentation(augmented_image, multi_aug)
            else:
                # Apply a single specific augmentation
                augmented_image = apply_augmentation(image, aug_type)

            augmented_samples.append((augmented_image, label))
    
    print(f"Finished generating. Total samples: {len(augmented_samples)}")
    return augmented_samples