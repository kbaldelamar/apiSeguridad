from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from typing import List, Optional

from models.person import Person
from models.user import User
from schemas.person import PersonCreate, PersonUpdate
from database import get_db

class PersonService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_person_by_id(self, person_id: int) -> Optional[Person]:
        """
        Obtiene una persona por su ID.
        
        Args:
            person_id: ID de la persona
            
        Returns:
            Optional[Person]: Persona encontrada o None
        """
        return self.db.query(Person).filter(Person.id == person_id).first()
    
    def get_person_by_user_id(self, user_id: int) -> Optional[Person]:
        """
        Obtiene la persona asociada a un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Optional[Person]: Persona asociada o None
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.person_id:
            return None
        
        return self.db.query(Person).filter(Person.id == user.person_id).first()
    
    def create_person(self, person_data: PersonCreate) -> Person:
        """
        Crea una nueva persona.
        
        Args:
            person_data: Datos de la persona
            
        Returns:
            Person: Persona creada
        """
        # Verificar si ya existe una persona con el mismo documento
        if person_data.document_number and person_data.document_type:
            existing = self.db.query(Person).filter(
                Person.document_type == person_data.document_type,
                Person.document_number == person_data.document_number
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe una persona con este documento"
                )
        
        # Crear la persona
        person = Person(**person_data.dict(exclude_unset=True))
        self.db.add(person)
        self.db.commit()
        self.db.refresh(person)
        
        return person
    
    def update_person(self, person_id: int, person_data: PersonUpdate) -> Optional[Person]:
        """
        Actualiza los datos de una persona.
        
        Args:
            person_id: ID de la persona
            person_data: Datos actualizados
            
        Returns:
            Optional[Person]: Persona actualizada o None si no existe
        """
        person = self.get_person_by_id(person_id)
        if not person:
            return None
        
        # Verificar si el documento ya está en uso por otra persona
        if person_data.document_number and person_data.document_type:
            existing = self.db.query(Person).filter(
                Person.document_type == person_data.document_type,
                Person.document_number == person_data.document_number,
                Person.id != person_id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe otra persona con este documento"
                )
        
        # Actualizar campos
        update_data = person_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(person, key, value)
        
        self.db.commit()
        self.db.refresh(person)
        
        return person
    
    def delete_person(self, person_id: int) -> bool:
        """
        Elimina una persona.
        
        Args:
            person_id: ID de la persona
            
        Returns:
            bool: True si se eliminó, False si no existe
        """
        person = self.get_person_by_id(person_id)
        if not person:
            return False
        
        # Verificar si está asociada a algún usuario
        user = self.db.query(User).filter(User.person_id == person_id).first()
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede eliminar una persona asociada a un usuario"
            )
        
        self.db.delete(person)
        self.db.commit()
        
        return True