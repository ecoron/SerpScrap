"""
The database schema.
There are four entities:
    ScraperSearch: Represents a search job.
    SearchEngineResultsPage: Represents a SERP result page of a search engine.
    Link: Represents a link on a SERP.
    Proxy: Stores all proxies and their statuses.
"""
import datetime
from urllib.parse import urlparse

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import backref, declarative_base, relationship, scoped_session, sessionmaker

Base = declarative_base()


def utc_now_naive():
    """Return UTC without timezone information for the legacy SQLite schema."""

    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

scraper_searches_serps = Table(
    'scraper_searches_serps',
    Base.metadata,
    Column('scraper_search_id', Integer, ForeignKey('scraper_search.id')),
    Column('serp_id', Integer, ForeignKey('serp.id'))
)


class ScraperSearch(Base):
    """Represents a search job, including metadata and associated SERPs."""
    __tablename__ = 'scraper_search'

    id = Column(Integer, primary_key=True)
    number_search_engines_used = Column(Integer)
    used_search_engines = Column(String)
    number_proxies_used = Column(Integer)
    number_search_queries = Column(Integer)
    started_searching = Column(DateTime, default=utc_now_naive)
    stopped_searching = Column(DateTime)

    serps = relationship(
        'SearchEngineResultsPage',
        secondary=scraper_searches_serps,
        backref=backref('scraper_searches', uselist=True)
    )

    def __str__(self):
        return (f"Search[{self.id}] scraped for {self.number_search_queries} unique keywords. "
                f"Started: {self.started_searching} and stopped: {self.stopped_searching}")

    def __repr__(self):
        return self.__str__()


class SearchEngineResultsPage(Base):
    """Represents a SERP result page of a search engine."""
    __tablename__ = 'serp'

    id = Column(Integer, primary_key=True)
    status = Column(String, default='successful')
    search_engine_name = Column(String)
    scrape_method = Column(String)
    page_number = Column(Integer)
    requested_at = Column(DateTime, default=utc_now_naive)
    requested_by = Column(String, default='127.0.0.1')

    num_results_for_query = Column(String, default='')
    num_results = Column(Integer, default=-1)
    query = Column(String)
    effective_query = Column(String, default='')
    no_results = Column(Boolean, default=False)

    def __str__(self):
        return (f"{self.search_engine_name} has [{self.num_results}] link results "
                f"for query \"{self.query}\"")

    def __repr__(self):
        return self.__str__()

    def has_no_results_for_query(self) -> bool:
        """Returns True if the original query did not yield any results."""
        return self.num_results == 0 or bool(self.effective_query)

    def set_values_from_parser(self, parser):
        """Populate itself from a parser object."""
        self.num_results_for_query = parser.num_results_for_query
        self.num_results = parser.num_results
        self.effective_query = parser.effective_query
        self.no_results = parser.no_results
        for key, value in parser.search_results.items():
            if isinstance(value, list):
                for link in value:
                    parsed = urlparse(link['link'])
                    if link['snippet'] is not None:
                        # Remove inline CSS if present
                        tmp_snipped = link['snippet'].split('}')
                        if len(tmp_snipped) > 1:
                            link['snippet'] = tmp_snipped[-1]
                    # Fill with None to prevent key errors
                    for k in ('snippet', 'title', 'visible_link', 'rating', 'sitelinks'):
                        link.setdefault(k, None)
                    Link(
                        link=link['link'],
                        snippet=link['snippet'],
                        title=link['title'],
                        visible_link=link['visible_link'],
                        domain=parsed.netloc,
                        rank=link['rank'],
                        serp=self,
                        link_type=key,
                        rating=link['rating'],
                        sitelinks=link['sitelinks']
                    )
        for _key, value in parser.related_keywords.items():
            if isinstance(value, list) and value:
                for keyword in value:
                    keyword.setdefault('keyword', None)
                    RelatedKeyword(
                        keyword=keyword['keyword'],
                        rank=keyword['rank'],
                        serp=self,
                    )

    def set_values_from_scraper(self, scraper):
        """Populate itself from a scraper object.

        A scraper may be any object of type:
            - SelScrape
        Args:
            A scraper object.
        """
        self.query = scraper.query
        self.search_engine_name = scraper.search_engine_name
        self.scrape_method = scraper.scrape_method
        self.page_number = scraper.page_number
        self.requested_at = scraper.requested_at
        self.requested_by = scraper.requested_by
        self.status = scraper.status

    def was_correctly_requested(self):
        return self.status == 'successful'


# Alias as a shorthand for working in the shell
SERP = SearchEngineResultsPage


class Link(Base):
    """Represents a link on a SERP."""
    __tablename__ = 'link'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    snippet = Column(String)
    link = Column(String)
    domain = Column(String)
    visible_link = Column(String)
    rank = Column(Integer)
    link_type = Column(String)
    rating = Column(String)
    sitelinks = Column(String)

    serp_id = Column(Integer, ForeignKey('serp.id'))
    serp = relationship(
        SearchEngineResultsPage,
        backref=backref('links', uselist=True)
    )

    def __str__(self):
        return f'<Link at rank {self.rank} has url: {self.link}>'

    def __repr__(self):
        return self.__str__()


class RelatedKeyword(Base):
    """Represents a related keyword found on a SERP."""
    __tablename__ = 'related_keywords'

    id = Column(Integer, primary_key=True)
    keyword = Column(String)
    rank = Column(Integer)

    serp_id = Column(Integer, ForeignKey('serp.id'))
    serp = relationship(
        SearchEngineResultsPage,
        backref=backref('related_keywords', uselist=True)
    )

    def __str__(self):
        return f'<related keyword at rank {self.rank} : {self.keyword}>'

    def __repr__(self):
        return self.__str__()


class Proxy(Base):
    """Stores all proxies and their statuses."""
    __tablename__ = 'proxy'

    id = Column(Integer, primary_key=True)
    ip = Column(String)
    hostname = Column(String)
    port = Column(Integer)
    proto = Column(Enum('socks5', 'socks4', 'http'))
    username = Column(String)
    password = Column(String)

    online = Column(Boolean)
    status = Column(String)
    checked_at = Column(DateTime)
    created_at = Column(DateTime, default=utc_now_naive)

    city = Column(String)
    region = Column(String)
    country = Column(String)
    loc = Column(String)
    org = Column(String)
    postal = Column(String)

    UniqueConstraint(ip, port, name='unique_proxy')

    def __str__(self):
        return f'<Proxy {self.ip}>'

    def __repr__(self):
        return self.__str__()


db_Proxy = Proxy


class SearchEngine(Base):
    """Represents a search engine configuration."""
    __tablename__ = 'search_engine'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    http_url = Column(String)
    selenium_url = Column(String)
    image_url = Column(String)


class SearchEngineProxyStatus(Base):
    """Stores last proxy status for the given search engine."""
    __tablename__ = 'search_engine_proxy_status'

    id = Column(Integer, primary_key=True)
    proxy_id = Column(Integer, ForeignKey('proxy.id'))
    search_engine_id = Column(Integer, ForeignKey('search_engine.id'))
    available = Column(Boolean)
    last_check = Column(DateTime)


def get_engine(config, path=None):
    """Return the SQLAlchemy engine for the configured database."""
    db_name = config.get('database_name', '/tmp/serpscrap') + '.db'
    db_path = path if path else db_name
    echo = config.get('log_sqlalchemy', False)
    engine = create_engine(
        'sqlite:///' + db_path,
        echo=echo,
        connect_args={'check_same_thread': False}
    )

    Base.metadata.create_all(engine)

    return engine


def get_session(config, scoped=False, engine=None, path=None):
    """Return a SQLAlchemy session factory or scoped session."""
    if not engine:
        engine = get_engine(config, path=path)

    session_factory = sessionmaker(
        bind=engine,
        autoflush=True,
        autocommit=False,
        expire_on_commit=False,
    )

    if scoped:
        ScopedSession = scoped_session(session_factory)
        return ScopedSession
    else:
        return session_factory


def fixtures(config, session):
    """Add base data for supported search engines if not present."""
    for se in config.get('supported_search_engines', []):
        if se and not session.query(SearchEngine).filter(SearchEngine.name == se).first():
            session.add(SearchEngine(name=se))
    session.commit()
