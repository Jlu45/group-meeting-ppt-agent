from setuptools import setup, find_packages

setup(
    name="group-meeting-ppt-agent",
    version="1.0.0",
    description="组会PPT自动制作智能体",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "markitdown>=0.1.0",
        "python-pptx>=1.0.0",
        "matplotlib>=3.8.0",
        "pandas>=2.1.0",
        "Pillow>=10.0.0",
        "openai>=1.0.0",
        "lxml>=5.0.0",
        "jinja2>=3.1.0",
    ],
    extras_require={
        "docling": ["docling>=2.0.0"],
        "dev": ["pytest>=7.0.0", "pytest-cov>=4.0.0"],
    },
    entry_points={
        "console_scripts": [
            "group-ppt=agent:main",
        ],
    },
)
