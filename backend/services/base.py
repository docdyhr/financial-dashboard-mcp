"""Base service class with common database operations."""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.base import Base

# Type variables
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base service class with common CRUD operations."""

    def __init__(self, model: type[ModelType]):
        """Initialize service with model class."""
        self.model = model

    def get(self, db: Session, id: Any) -> ModelType | None:
        """Get a single record by ID."""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_by_field(
        self, db: Session, field_name: str, field_value: Any
    ) -> ModelType | None:
        """Get a single record by field name and value."""
        return (
            db.query(self.model)
            .filter(getattr(self.model, field_name) == field_value)
            .first()
        )

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
    ) -> list[ModelType]:
        """Get multiple records with optional filtering and pagination."""
        query = db.query(self.model)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.filter(getattr(self.model, field) == value)

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))

        return query.offset(skip).limit(limit).all()

    def count(self, db: Session, *, filters: dict[str, Any] | None = None) -> int:
        """Count records with optional filtering."""
        query = db.query(self.model)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.filter(getattr(self.model, field) == value)

        return query.count()

    def create(
        self, db: Session, *, obj_in: CreateSchemaType | dict[str, Any]
    ) -> ModelType:
        """Create a new record."""
        obj_in_data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        """Update an existing record."""
        obj_data = db_obj.__dict__.copy()

        if hasattr(obj_in, "dict"):
            update_data = obj_in.dict(exclude_unset=True)
        else:
            update_data = obj_in

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> ModelType | None:
        """Delete a record by ID."""
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def soft_delete(self, db: Session, *, id: int) -> ModelType | None:
        """Soft delete a record by setting is_active to False."""
        obj = db.query(self.model).get(id)
        if obj and hasattr(obj, "is_active"):
            obj.is_active = False
            db.add(obj)
            db.commit()
            db.refresh(obj)
        return obj

    def bulk_create(
        self, db: Session, *, objs_in: list[CreateSchemaType | dict[str, Any]]
    ) -> list[ModelType]:
        """Create multiple records."""
        db_objs = []
        for obj_in in objs_in:
            obj_in_data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)

        db.add_all(db_objs)
        db.commit()
        for db_obj in db_objs:
            db.refresh(db_obj)
        return db_objs

    def exists(self, db: Session, *, id: int) -> bool:
        """Check if a record exists by ID."""
        return db.query(self.model).filter(self.model.id == id).first() is not None

    def exists_by_field(self, db: Session, field_name: str, field_value: Any) -> bool:
        """Check if a record exists by field name and value."""
        return (
            db.query(self.model)
            .filter(getattr(self.model, field_name) == field_value)
            .first()
            is not None
        )

    def get_or_create(
        self, db: Session, *, defaults: dict[str, Any] | None = None, **kwargs
    ) -> tuple[ModelType, bool]:
        """Get an existing record or create a new one."""
        # Try to get existing record
        query = db.query(self.model)
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)

        instance = query.first()

        if instance:
            return instance, False

        # Create new record
        params = kwargs.copy()
        if defaults:
            params.update(defaults)

        try:
            instance = self.model(**params)
            db.add(instance)
            db.commit()
            db.refresh(instance)
            return instance, True
        except IntegrityError:
            db.rollback()
            # Try to get the record again in case it was created by another process
            instance = query.first()
            if instance:
                return instance, False
            raise

    def filter_by_ids(self, db: Session, *, ids: list[int]) -> list[ModelType]:
        """Get multiple records by a list of IDs."""
        return db.query(self.model).filter(self.model.id.in_(ids)).all()

    def search(
        self,
        db: Session,
        *,
        search_term: str,
        search_fields: list[str],
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """Search records by term in specified fields."""
        query = db.query(self.model)

        # Build search conditions
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                field_obj = getattr(self.model, field)
                search_conditions.append(field_obj.ilike(f"%{search_term}%"))

        if search_conditions:
            from sqlalchemy import or_

            query = query.filter(or_(*search_conditions))

        return query.offset(skip).limit(limit).all()

    def get_active(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """Get active records (where is_active=True)."""
        if not hasattr(self.model, "is_active"):
            return self.get_multi(db, skip=skip, limit=limit)

        return (
            db.query(self.model)
            .filter(self.model.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def batch_update(
        self, db: Session, *, ids: list[int], update_data: dict[str, Any]
    ) -> list[ModelType]:
        """Update multiple records by IDs."""
        objects = db.query(self.model).filter(self.model.id.in_(ids)).all()

        for obj in objects:
            for field, value in update_data.items():
                if hasattr(obj, field):
                    setattr(obj, field, value)

        db.commit()

        for obj in objects:
            db.refresh(obj)

        return objects
