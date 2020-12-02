# Collector Abstracts
There are 3 classes of abstract collectors:
* [AbstractCollectr](##AbstractCollectr)
    * The base class for the other two    
* [`RequestCollectr`]()
    * Uses the `requests` and `BeautifulSoup` modules to collect data.
    * This is for webpages that do either:
        * Has a API
        * Doesn't Use Javascript
* `SeleniumCollectr`
    * Uses the `selenium` module to collect data.
    * This is for webpages that both:
        * doesn't have an API
        * Uses Javascript

## AbstractCollectr
### `__init__`
### Site
### Person

## RequestCollectr

## SeleniumCollectr