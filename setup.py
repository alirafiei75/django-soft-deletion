from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="django-soft-deletion-model",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["Django==4.2"],
    license="MIT",
    description="A Django-based library for implementing soft deletion using a deleted_at timestamp.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ali Rafiei",
    author_email="a.rafiei1375@gmail.com",
    url="https://github.com/alirafiei75/django-soft-deletion",
    classifiers=[
        "Framework :: Django",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
    ],
)
