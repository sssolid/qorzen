from __future__ import annotations
from typing import Union
'\nMODNet model implementation for background removal.\n\nThis file contains the model architecture for the MODNet model,\nas described in the paper "Is a Green Screen Really Necessary for Real-Time Portrait Matting?"\nby Ke et al.\n'
import torch
import torch.nn as nn
import torch.nn.functional as F
class IBNorm(nn.Module):
    def __init__(self, dim: int) -> None:
        super(IBNorm, self).__init__()
        half = dim // 2
        self.instance = nn.InstanceNorm2d(half, affine=True)
        self.batch = nn.BatchNorm2d(dim - half)
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        split = torch.split(x, x.shape[1] // 2, 1)
        return torch.cat([self.instance(split[0]), self.batch(split[1])], 1)
class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int=3, stride: int=1, padding: int=1, dilation: int=1, groups: int=1, bias: bool=False, norm: str='bn', activation: str='relu') -> None:
        super(ConvBlock, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, dilation, groups, bias)
        if norm == 'bn':
            self.norm = nn.BatchNorm2d(out_channels)
        elif norm == 'in':
            self.norm = nn.InstanceNorm2d(out_channels, affine=True)
        elif norm == 'ibn':
            self.norm = IBNorm(out_channels)
        elif norm == 'none':
            self.norm = nn.Identity()
        else:
            raise ValueError(f'Unsupported normalization: {norm}')
        if activation == 'relu':
            self.activation = nn.ReLU(inplace=True)
        elif activation == 'leaky_relu':
            self.activation = nn.LeakyReLU(0.2, inplace=True)
        elif activation == 'tanh':
            self.activation = nn.Tanh()
        elif activation == 'sigmoid':
            self.activation = nn.Sigmoid()
        elif activation == 'none':
            self.activation = nn.Identity()
        else:
            raise ValueError(f'Unsupported activation: {activation}')
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv(x)
        x = self.norm(x)
        x = self.activation(x)
        return x
class ResBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, stride: int=1, padding: int=1, dilation: int=1, norm: str='bn') -> None:
        super(ResBlock, self).__init__()
        self.conv1 = ConvBlock(in_channels, out_channels // 4, 1, 1, 0, norm=norm)
        self.conv2 = ConvBlock(out_channels // 4, out_channels // 4, 3, stride, padding, dilation, norm=norm)
        self.conv3 = ConvBlock(out_channels // 4, out_channels, 1, 1, 0, norm=norm, activation='none')
        if in_channels != out_channels or stride != 1:
            self.shortcut = ConvBlock(in_channels, out_channels, 1, stride, 0, norm=norm, activation='none')
        else:
            self.shortcut = nn.Identity()
        self.activation = nn.ReLU(inplace=True)
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.shortcut(x)
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        return self.activation(x + residual)
class MODNetBackbone(nn.Module):
    def __init__(self) -> None:
        super(MODNetBackbone, self).__init__()
        self.enc_conv1 = ConvBlock(3, 32, kernel_size=3, stride=2, padding=1, norm='bn')
        self.enc_conv2 = ConvBlock(32, 64, kernel_size=3, stride=1, padding=1, norm='bn')
        self.block1 = nn.Sequential(ResBlock(64, 256, stride=2, norm='bn'), ResBlock(256, 256, stride=1, norm='bn'), ResBlock(256, 256, stride=1, norm='bn'))
        self.block2 = nn.Sequential(ResBlock(256, 512, stride=2, norm='bn'), ResBlock(512, 512, stride=1, norm='bn'), ResBlock(512, 512, stride=1, norm='bn'), ResBlock(512, 512, stride=1, norm='bn'))
        self.block3 = nn.Sequential(ResBlock(512, 1024, stride=2, norm='ibn'), ResBlock(1024, 1024, stride=1, norm='ibn'), ResBlock(1024, 1024, stride=1, norm='ibn'), ResBlock(1024, 1024, stride=1, norm='ibn'), ResBlock(1024, 1024, stride=1, norm='ibn'), ResBlock(1024, 1024, stride=1, norm='ibn'))
        self.block4 = nn.Sequential(ResBlock(1024, 2048, stride=2, norm='bn'), ResBlock(2048, 2048, stride=1, norm='bn'), ResBlock(2048, 2048, stride=1, norm='bn'))
    def forward(self, x: torch.Tensor) -> tuple:
        x0 = self.enc_conv1(x)
        x1 = self.enc_conv2(x0)
        x2 = self.block1(x1)
        x3 = self.block2(x2)
        x4 = self.block3(x3)
        x5 = self.block4(x4)
        return (x0, x1, x2, x3, x4, x5)
class MODNetDecoder(nn.Module):
    def __init__(self) -> None:
        super(MODNetDecoder, self).__init__()
        self.dec_conv5 = ConvBlock(2048, 512, kernel_size=3, padding=1, norm='bn')
        self.dec_conv4 = ConvBlock(1024, 256, kernel_size=3, padding=1, norm='bn')
        self.dec_conv3 = ConvBlock(512, 128, kernel_size=3, padding=1, norm='bn')
        self.dec_conv2 = ConvBlock(256, 64, kernel_size=3, padding=1, norm='bn')
        self.dec_conv1 = ConvBlock(128, 32, kernel_size=3, padding=1, norm='bn')
        self.dec_out = nn.Conv2d(32, 1, 1)
    def forward(self, features: tuple) -> torch.Tensor:
        x0, x1, x2, x3, x4, x5 = features
        x = self.dec_conv5(x5)
        x = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=False)
        x = torch.cat([x, x4], dim=1)
        x = self.dec_conv4(x)
        x = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=False)
        x = torch.cat([x, x3], dim=1)
        x = self.dec_conv3(x)
        x = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=False)
        x = torch.cat([x, x2], dim=1)
        x = self.dec_conv2(x)
        x = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=False)
        x = torch.cat([x, x1], dim=1)
        x = self.dec_conv1(x)
        alpha_matte = self.dec_out(x)
        return alpha_matte
class MODNet(nn.Module):
    def __init__(self) -> None:
        super(MODNet, self).__init__()
        self.backbone = MODNetBackbone()
        self.decoder = MODNetDecoder()
    def forward(self, x: torch.Tensor, inference: bool=False) -> Union[torch.Tensor, tuple]:
        features = self.backbone(x)
        alpha_matte = self.decoder(features)
        alpha_matte = torch.sigmoid(alpha_matte)
        if inference:
            return alpha_matte
        return alpha_matte