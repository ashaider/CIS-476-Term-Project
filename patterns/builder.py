# Builder pattern - CarListingBuilder
#
# Separates required fields (make, model, year, price, location, dates)
# from optional ones (mileage, transmission, seats, description, image).
# Each setter returns self so you can chain them.
# build() validates that required fields are set and returns a dict
# that gets unpacked directly into the Car model constructor.
#
# build_car_from_form() is the director - it takes the submitted form
# data and calls the builder methods in the right order.

from abc import ABC, abstractmethod
from datetime import date


class AbstractCarListingBuilder(ABC):

    @abstractmethod
    def set_make(self, make: str): pass

    @abstractmethod
    def set_model(self, model: str): pass

    @abstractmethod
    def set_year(self, year: int): pass

    @abstractmethod
    def set_price_per_day(self, price: float): pass

    @abstractmethod
    def set_location(self, location: str): pass

    @abstractmethod
    def set_availability(self, from_date: date, to_date: date): pass

    # Optional - default implementations do nothing
    def set_mileage(self, mileage: str): pass
    def set_transmission(self, transmission: str): pass
    def set_seats(self, seats: int): pass
    def set_description(self, description: str): pass
    def set_image_url(self, url: str): pass

    @abstractmethod
    def build(self) -> dict: pass


class CarListingBuilder(AbstractCarListingBuilder):

    def __init__(self, owner_id: int):
        self._owner_id = owner_id
        self._reset()

    def _reset(self):
        # Required fields start as None so build() can catch missing ones
        self._make           = None
        self._model          = None
        self._year           = None
        self._price_per_day  = None
        self._location       = None
        self._available_from = None
        self._available_to   = None
        # Optional fields get sensible defaults
        self._mileage        = "Not specified"
        self._transmission   = "Automatic"
        self._seats          = 5
        self._description    = ""
        self._image_url      = ""

    # Required setters
    def set_make(self, make: str):
        self._make = make.strip()
        return self

    def set_model(self, model: str):
        self._model = model.strip()
        return self

    def set_year(self, year: int):
        self._year = int(year)
        return self

    def set_price_per_day(self, price: float):
        self._price_per_day = float(price)
        return self

    def set_location(self, location: str):
        self._location = location.strip()
        return self

    def set_availability(self, from_date: date, to_date: date):
        self._available_from = from_date
        self._available_to   = to_date
        return self

    # Optional setters
    def set_mileage(self, mileage: str):
        if mileage:
            self._mileage = mileage.strip()
        return self

    def set_transmission(self, transmission: str):
        if transmission:
            self._transmission = transmission
        return self

    def set_seats(self, seats: int):
        if seats:
            self._seats = int(seats)
        return self

    def set_description(self, description: str):
        if description:
            self._description = description.strip()
        return self

    def set_image_url(self, url: str):
        if url:
            self._image_url = url.strip()
        return self

    def build(self) -> dict:
        # Make sure nothing required was skipped
        missing = []
        if not self._make:           missing.append("make")
        if not self._model:          missing.append("model")
        if not self._year:           missing.append("year")
        if not self._price_per_day:  missing.append("price_per_day")
        if not self._location:       missing.append("location")
        if not self._available_from: missing.append("available_from")
        if not self._available_to:   missing.append("available_to")

        if missing:
            raise ValueError(f"Missing required car listing fields: {', '.join(missing)}")

        if self._available_from > self._available_to:
            raise ValueError("available_from must be before available_to")

        result = {
            "owner_id":       self._owner_id,
            "make":           self._make,
            "model":          self._model,
            "year":           self._year,
            "price_per_day":  self._price_per_day,
            "location":       self._location,
            "available_from": self._available_from,
            "available_to":   self._available_to,
            "mileage":        self._mileage,
            "transmission":   self._transmission,
            "seats":          self._seats,
            "description":    self._description,
            "image_url":      self._image_url,
            "is_available":   True,
        }

        self._reset()
        return result


def build_car_from_form(owner_id: int, form_data: dict) -> dict:
    # Director - called by the add/edit car routes after form submission
    from datetime import date

    available_from = date.fromisoformat(form_data["available_from"])
    available_to   = date.fromisoformat(form_data["available_to"])

    builder = CarListingBuilder(owner_id)

    (builder
        .set_make(form_data["make"])
        .set_model(form_data["model"])
        .set_year(form_data["year"])
        .set_price_per_day(form_data["price_per_day"])
        .set_location(form_data["location"])
        .set_availability(available_from, available_to)
    )

    builder.set_mileage(form_data.get("mileage", ""))
    builder.set_transmission(form_data.get("transmission", "Automatic"))
    builder.set_seats(form_data.get("seats", 5))
    builder.set_description(form_data.get("description", ""))
    builder.set_image_url(form_data.get("image_url", ""))

    return builder.build()
