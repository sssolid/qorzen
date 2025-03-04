from setuptools import find_packages, setup

setup(
    name="qorzen",
    version="0.1.0",
    author="Qorzen",
    author_email="contact@qorzen.com",
    description="Qorzen - A modular microkernel-based platform",
    long_description="This is a placeholder package to reserve the name 'Qorzen' on PyPI.",
    long_description_content_type="text/plain",
    url="https://qorzen.com",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
)
