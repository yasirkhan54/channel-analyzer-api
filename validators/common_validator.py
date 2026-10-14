from pydantic import AliasGenerator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


class StoredRecordResponse(BaseModel):
    """Built from Prisma models (camelCase attributes); serialized with snake_case field names."""

    model_config = ConfigDict(from_attributes=True, alias_generator=AliasGenerator(validation_alias=to_camel))


class PageQuery(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size


class Page[T](BaseModel):
    items: list[T]
    page: int
    page_size: int
    total: int


class ErrorResponse(BaseModel):
    detail: str
