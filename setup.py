from setuptools import setup, find_packages

setup(
    name="Daily Language Telegram Bot",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'daily-language-bot-app = daily_language_bot.__main__:main',
        ],
    },
    package_data={
        'my_package': ['config/*.txt'],
    },
    include_package_data=True,
)