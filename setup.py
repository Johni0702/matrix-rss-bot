from setuptools import setup

setup(
    name='matrix-rss-bot',
    version='0.0.0',
    author='Jonas Herzig',
    author_email='me@johni0702.de',
    description='A stateless [Matrix] bot which serves RSS feeds into rooms.',
    license='GPL3',
    url='https://github.com/Johni0702/matrix-rss-bot',
    install_requires=[
        'matrix-client>=0.3',
        'feedparser>=5.2',
    ],
    scripts=['rssbot.py'],
)
