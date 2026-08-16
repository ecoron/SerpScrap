<!-- :orphan: -->

# Alpha 2.0.0: Topic Tools and `TopicPlugin`

## Ziel

SerpScrap soll neben allgemeinen Web-Suchergebnissen auch thematische
Suchwerkzeuge anbieten. News, Shopping und spätere Bereiche wie Jobs, Reisen
oder Veranstaltungen sollen dieselben technischen Grundlagen verwenden,
ohne ihre domänenspezifische Logik zu verlieren.

Der bestehende `SearchEnginePlugin` bleibt kompatibel. `TopicPlugin` bildet
eine gemeinsame Erweiterungsschicht für thematische Quellen.

## Architektur

```text
TopicPlugin
├── SearchTopicPlugin       allgemeine Suchmaschinen
├── NewsSourcePlugin        Nachrichten und Feeds
├── ShoppingSourcePlugin    Marktplätze und Preisvergleiche
└── weitere Themen           Jobs, Reisen, Events, Bücher ...
```

Der gemeinsame Lebenszyklus besteht aus:

1. Anfrage validieren und capabilities prüfen
2. Quellen aus einer Registry auswählen
3. URL oder Transport-Anfrage erstellen
4. Antwort über HTTP, Browser oder Feed-Adapter laden
5. quellen-spezifisch parsen
6. Ergebnisse normalisieren und klassifizieren
7. Duplikate und Varianten behandeln
8. Filter und thematisches Ranking anwenden
9. standardisierten Report mit Quellen- und Fehler-Metadaten erzeugen

Gemeinsame Infrastruktur bleibt im Kern: Retry, Rate Limits, Blockierungs-
und Consent-Erkennung, Pagination, Caching, Diagnostik, Persistenz und
Fehlerberichte.

## Vertrag

```python
class TopicPlugin(ABC):
    topic_id: ClassVar[str]
    display_name: ClassVar[str]
    capabilities: TopicCapabilities

    def build_request(self, request: TopicRequest) -> TopicRequest: ...
    def build_url(self, request: TopicRequest, *, page: int) -> str: ...
    def parse(self, payload: str, *, request: TopicRequest, page: int) -> list[TopicResult]: ...
    def normalize(self, result: TopicResult) -> TopicResult: ...
    def classify(self, payload: str) -> str | None: ...
```

`TopicCapabilities` beschreibt mindestens Suchtypen, Länder, Sprachen,
Transport, Pagination und den Reifegrad (`enabled`, `experimental`,
`disabled`). Ein Plugin darf themenspezifische Felder, Filter und Ranking-
Regeln ergänzen, muss aber die gemeinsame Fehler- und Metadatenstruktur
einhalten.

## Standardisierte Modelle

Die Basismodelle sollten folgende Informationen tragen:

- `TopicRequest`: Query, Quellen, Land, Sprache, Zeitraum und Filter
- `TopicResult`: URL, Titel, Kurztext, Quelle, Rang und Zeitstempel
- `TopicReport`: Ergebnisse, Quellenstatus, Fehler, Laufzeit und Schema-Version

News ergänzt insbesondere `published_at`, Autor, Kategorie, Sprache und
Ereignisgruppe. Shopping ergänzt Preis, Währung, Händler, Verfügbarkeit,
Bewertung, Produkt-ID und GTIN. Roh-URL und kanonische URL werden immer
getrennt erhalten.

## News-Umsetzung

News-Quellen können Nachrichtenportale, Aggregatoren sowie RSS- und Atom-
Feeds sein. Die erste Version sollte Feeds und stabile Suchoberflächen
bevorzugen. Zentrale Funktionen sind:

- Zeitraum-, Länder- und Sprachfilter
- Aktualitätsbewertung
- Erkennung nahezu identischer Meldungen
- Gruppierung derselben Meldung zu einem Ereignis
- Quellenvielfalt und syndizierte Inhalte sichtbar machen
- Erhalt von Veröffentlichungszeit, Quelle und Original-URL

Ein News-Plugin darf einen Feed-Transport verwenden, während ein anderes den
Browser-Transport benötigt. Der gemeinsame Service muss beide Varianten
gleich behandeln.

## Shopping-Umsetzung

Shopping-Quellen liefern Marktplatz- oder Preisvergleichsergebnisse. Die
Normalisierung behandelt Preis, Versand, Währung, Verfügbarkeit, Varianten
und Produkt-IDs. Deduplizierung nutzt bevorzugt GTIN, Hersteller-/Modellnummer
und erst danach einen normalisierten Produkttitel.

## Registry und Schnittstellen

Eine `TopicPluginRegistry` registriert Plugins, validiert Verträge und findet
Quellen nach Topic, Land, Sprache und Transport. CLI, HTTP-API und MCP greifen
auf denselben `TopicService` zu; keine Schnittstelle implementiert eigene
Scraping- oder Ranking-Logik.

Beispielhafte spätere Aufrufe:

```text
serpscrap news "künstliche intelligenz" --language de --since 24h
serpscrap shopping "noise cancelling kopfhörer" --currency EUR
```

## Umsetzungsplan

### Phase 1: Kernvertrag

- `TopicRequest`, `TopicResult`, `TopicReport` und `TopicCapabilities` entwerfen
- Plugin-Lifecycle, Statuswerte und Metadaten definieren
- Registry mit Contract-Validation ergänzen
- bestehende `SearchEnginePlugin`-Metadaten anschlussfähig machen

### Phase 2: Gemeinsame Verarbeitung

- URL-, Redirect- und Tracking-Normalisierung vereinheitlichen
- gemeinsame Fehlerklassen und Source-Status einführen
- Pagination, Retry, Rate Limits, Cache und Diagnostik anbinden
- themenunabhängige Deduplizierungs-Schnittstelle bereitstellen

### Phase 3: News-MVP

- News-Modelle und Feed-Adapter implementieren
- Veröffentlichungszeit, Sprache und Quelle normalisieren
- Zeitraumfilter, Aktualitätsranking und Artikel-Deduplizierung ergänzen
- Fixture-basierte Parser- und Fehlerzustandstests hinzufügen

### Phase 4: Shopping-MVP

- Shopping-Modelle und locale-sicheren Preisparser implementieren
- Händler, Währung, Verfügbarkeit und Versandkosten normalisieren
- Produkt-Fingerprints, Variantenbehandlung und Preisfilter ergänzen

### Phase 5: Produktintegration

- CLI-, API- und MCP-Funktionen über `TopicService` veröffentlichen
- Ergebnis-Persistenz und bestehende `serp_type`-Darstellung erweitern
- UI für Topic-Auswahl, Filter und Source-Status ergänzen
- Schema-Versionierung und Rückwärtskompatibilität prüfen

### Phase 6: Qualität und Erweiterbarkeit

- Contract-Test-Suite für jedes Plugin automatisieren
- Sanitized Fixtures und Parser-Regressionstests etablieren
- Plugin-Dokumentation und Beispieladapter bereitstellen
- Jobs, Reisen oder Events nur über denselben Vertrag ergänzen

## Sicherheits- und Betriebsregeln

Quellen werden nicht automatisch mit CAPTCHA-, Consent- oder Rate-Limit-
Mechanismen umgangen. Robots-Regeln, Nutzungsbedingungen, offizielle APIs,
Rate Limits und personenbezogene Daten müssen pro Quelle geprüft werden.
Rohantworten mit Query- oder Session-Daten gehören nicht in Repository oder
CI-Artefakte.

## Abnahmekriterien

- neue Themenquelle benötigt nur Plugin, Parser, Fixture und Tests
- bestehende Suchmaschinenfunktion bleibt API-kompatibel
- alle Quellen liefern denselben Report- und Fehlervertrag
- News- und Shopping-Ergebnisse lassen sich gemeinsam persistieren und filtern
- CLI, API und MCP verwenden denselben Service
- deterministische Tests laufen ohne Netzwerk im Pipenv-Testlauf
