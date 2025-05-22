from __future__ import annotations
'\nISNet model implementation for background removal.\n\nThis file contains the model architecture for the ISNet model,\nas described in the paper "Highly Accurate Dichotomous Image Segmentation"\nby Qin et al.\n'
import torch
import torch.nn as nn
import torch.nn.functional as F
def conv_bn_relu(in_ch: int, out_ch: int, kernel_size: int=3, stride: int=1, padding: int=1, dilation: int=1) -> nn.Sequential:
    return nn.Sequential(nn.Conv2d(in_ch, out_ch, kernel_size=kernel_size, stride=stride, padding=padding, dilation=dilation, bias=False), nn.BatchNorm2d(out_ch), nn.ReLU(inplace=True))
class ResidualConv(nn.Module):
    def __init__(self, in_ch: int, out_ch: int) -> None:
        super(ResidualConv, self).__init__()
        self.conv1 = conv_bn_relu(in_ch, out_ch)
        self.conv2 = conv_bn_relu(out_ch, out_ch)
        if in_ch != out_ch:
            self.skip = nn.Conv2d(in_ch, out_ch, kernel_size=1, bias=False)
        else:
            self.skip = None
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        out = self.conv1(x)
        out = self.conv2(out)
        if self.skip is not None:
            residual = self.skip(x)
        return out + residual
class ISNetEncoder(nn.Module):
    def __init__(self, in_ch: int, depth: int=64) -> None:
        super(ISNetEncoder, self).__init__()
        self.conv1 = conv_bn_relu(in_ch, depth, kernel_size=3, padding=1)
        self.res1 = ResidualConv(depth, depth)
        self.pool1 = nn.MaxPool2d(2, stride=2)
        self.conv2 = conv_bn_relu(depth, depth * 2, kernel_size=3, padding=1)
        self.res2 = ResidualConv(depth * 2, depth * 2)
        self.pool2 = nn.MaxPool2d(2, stride=2)
        self.conv3 = conv_bn_relu(depth * 2, depth * 4, kernel_size=3, padding=1)
        self.res3 = ResidualConv(depth * 4, depth * 4)
        self.pool3 = nn.MaxPool2d(2, stride=2)
        self.conv4 = conv_bn_relu(depth * 4, depth * 8, kernel_size=3, padding=1)
        self.res4 = ResidualConv(depth * 8, depth * 8)
        self.pool4 = nn.MaxPool2d(2, stride=2)
        self.conv5 = conv_bn_relu(depth * 8, depth * 16, kernel_size=3, padding=1)
        self.res5 = ResidualConv(depth * 16, depth * 16)
    def forward(self, x: torch.Tensor) -> tuple:
        x1 = self.conv1(x)
        x1 = self.res1(x1)
        p1 = self.pool1(x1)
        x2 = self.conv2(p1)
        x2 = self.res2(x2)
        p2 = self.pool2(x2)
        x3 = self.conv3(p2)
        x3 = self.res3(x3)
        p3 = self.pool3(x3)
        x4 = self.conv4(p3)
        x4 = self.res4(x4)
        p4 = self.pool4(x4)
        x5 = self.conv5(p4)
        x5 = self.res5(x5)
        return (x1, x2, x3, x4, x5)
class ISNetDecoder(nn.Module):
    def __init__(self, depth: int=64) -> None:
        super(ISNetDecoder, self).__init__()
        self.up4 = nn.ConvTranspose2d(depth * 16, depth * 8, kernel_size=2, stride=2)
        self.conv4d = conv_bn_relu(depth * 16, depth * 8)
        self.res4d = ResidualConv(depth * 8, depth * 8)
        self.up3 = nn.ConvTranspose2d(depth * 8, depth * 4, kernel_size=2, stride=2)
        self.conv3d = conv_bn_relu(depth * 8, depth * 4)
        self.res3d = ResidualConv(depth * 4, depth * 4)
        self.up2 = nn.ConvTranspose2d(depth * 4, depth * 2, kernel_size=2, stride=2)
        self.conv2d = conv_bn_relu(depth * 4, depth * 2)
        self.res2d = ResidualConv(depth * 2, depth * 2)
        self.up1 = nn.ConvTranspose2d(depth * 2, depth, kernel_size=2, stride=2)
        self.conv1d = conv_bn_relu(depth * 2, depth)
        self.res1d = ResidualConv(depth, depth)
        self.side1 = nn.Conv2d(depth, 1, kernel_size=3, padding=1)
        self.side2 = nn.Conv2d(depth * 2, 1, kernel_size=3, padding=1)
        self.side3 = nn.Conv2d(depth * 4, 1, kernel_size=3, padding=1)
        self.side4 = nn.Conv2d(depth * 8, 1, kernel_size=3, padding=1)
        self.side5 = nn.Conv2d(depth * 16, 1, kernel_size=3, padding=1)
        self.fusion = nn.Conv2d(5, 1, kernel_size=1)
    def forward(self, features: tuple) -> torch.Tensor:
        x1, x2, x3, x4, x5 = features
        side5 = self.side5(x5)
        side5_up = F.interpolate(side5, size=x1.shape[2:], mode='bilinear', align_corners=True)
        x4d = self.up4(x5)
        x4d = torch.cat([x4, x4d], dim=1)
        x4d = self.conv4d(x4d)
        x4d = self.res4d(x4d)
        side4 = self.side4(x4d)
        side4_up = F.interpolate(side4, size=x1.shape[2:], mode='bilinear', align_corners=True)
        x3d = self.up3(x4d)
        x3d = torch.cat([x3, x3d], dim=1)
        x3d = self.conv3d(x3d)
        x3d = self.res3d(x3d)
        side3 = self.side3(x3d)
        side3_up = F.interpolate(side3, size=x1.shape[2:], mode='bilinear', align_corners=True)
        x2d = self.up2(x3d)
        x2d = torch.cat([x2, x2d], dim=1)
        x2d = self.conv2d(x2d)
        x2d = self.res2d(x2d)
        side2 = self.side2(x2d)
        side2_up = F.interpolate(side2, size=x1.shape[2:], mode='bilinear', align_corners=True)
        x1d = self.up1(x2d)
        x1d = torch.cat([x1, x1d], dim=1)
        x1d = self.conv1d(x1d)
        x1d = self.res1d(x1d)
        side1 = self.side1(x1d)
        fusion = self.fusion(torch.cat([side1, side2_up, side3_up, side4_up, side5_up], dim=1))
        return (fusion, side1, side2_up, side3_up, side4_up, side5_up)
class ISNetDIS(nn.Module):
    def __init__(self, in_ch: int=3, out_ch: int=1, depth: int=64) -> None:
        super(ISNetDIS, self).__init__()
        self.encoder = ISNetEncoder(in_ch, depth)
        self.decoder = ISNetDecoder(depth)
    def forward(self, x: torch.Tensor) -> tuple:
        features = self.encoder(x)
        outputs = self.decoder(features)
        outputs_sigmoid = []
        for output in outputs:
            outputs_sigmoid.append(torch.sigmoid(output))
        return outputs_sigmoid