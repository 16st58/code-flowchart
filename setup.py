# setup.py
from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="code_flowchart",                # PyPI에 올릴 패키지명
    version="0.1.0",                      # 버전
    description="A simple tool for creating flowcharts of code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="16st58",
    author_email="kithree1010@gmail.com",
    url="https://github.com/16st58/code-flowchart",
    packages=find_packages(),             # __init__.py가 있는 폴더를 패키지로 인식
    install_requires=[
        "graphviz",
    ],
    entry_points={
        "console_scripts": [
            # code_flowchart 명령으로 실행하면 cli.py의 main 함수를 실행
            "code_flowchart=code_flowchart.cli:main"
        ]
    },
    python_requires=">=3.0",  # 사용 가능한 파이썬 버전 명시
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
