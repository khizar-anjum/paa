"""
Vector Store Service using ChromaDB for semantic search
Handles embedding and retrieval of conversations, habits, people, and commitments.
"""

import os
import uuid
from typing import Dict, List, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

import database as models


class VectorStore:
    """
    Manages ChromaDB collections for semantic search across different data types.
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client and collections"""
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Use ChromaDB's default embedding function (no external API needed)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Initialize collections
        self.conversations_collection = self._get_or_create_collection("conversations")
        self.habits_collection = self._get_or_create_collection("habits")
        self.people_collection = self._get_or_create_collection("people")
        self.commitments_collection = self._get_or_create_collection("commitments")
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        try:
            return self.client.get_collection(name, embedding_function=self.embedding_fn)
        except Exception:
            return self.client.create_collection(name, embedding_function=self.embedding_fn)
    
    def embed_conversation(self, conversation: models.Conversation):
        """Add a conversation to the vector store"""
        try:
            # Create combined text for embedding
            combined_text = f"User: {conversation.message}\nAI: {conversation.response}"
            
            self.conversations_collection.add(
                documents=[combined_text],
                metadatas=[{
                    "user_id": conversation.user_id,
                    "conversation_id": conversation.id,
                    "timestamp": conversation.timestamp.isoformat(),
                    "user_message": conversation.message,
                    "ai_response": conversation.response
                }],
                ids=[f"conv_{conversation.id}"]
            )
        except Exception as e:
            print(f"Error embedding conversation {conversation.id}: {e}")
    
    def embed_habit(self, habit: models.Habit, db: Session):
        """Add a habit to the vector store with context"""
        try:
            # Get recent completions for context
            recent_logs = db.query(models.HabitLog).filter(
                models.HabitLog.habit_id == habit.id
            ).order_by(models.HabitLog.completed_at.desc()).limit(10).all()
            
            completion_context = ""
            if recent_logs:
                completion_dates = [log.completed_at.strftime('%Y-%m-%d') for log in recent_logs]
                completion_context = f" Recent completions: {', '.join(completion_dates)}"
            
            # Create text for embedding
            habit_text = f"Habit: {habit.name}"
            if hasattr(habit, 'description') and habit.description:
                habit_text += f" - {habit.description}"
            habit_text += f" Frequency: {habit.frequency} times per day{completion_context}"
            
            self.habits_collection.add(
                documents=[habit_text],
                metadatas=[{
                    "user_id": habit.user_id,
                    "habit_id": habit.id,
                    "name": habit.name,
                    "description": getattr(habit, 'description', "") or "",
                    "frequency": habit.frequency,
                    "is_active": habit.is_active,
                    "created_at": habit.created_at.isoformat()
                }],
                ids=[f"habit_{habit.id}"]
            )
        except Exception as e:
            print(f"Error embedding habit {habit.id}: {e}")
    
    def embed_person(self, person: models.Person):
        """Add a person to the vector store"""
        try:
            # Create text for embedding
            person_text = f"Person: {person.name}"
            if person.how_you_know_them:
                person_text += f" - {person.how_you_know_them}"
            if person.pronouns:
                person_text += f" (Pronouns: {person.pronouns})"
            if person.description:
                person_text += f" {person.description}"
            
            self.people_collection.add(
                documents=[person_text],
                metadatas=[{
                    "user_id": person.user_id,
                    "person_id": person.id,
                    "name": person.name,
                    "relationship": person.how_you_know_them or "",
                    "pronouns": person.pronouns or "",
                    "description": person.description or "",
                    "created_at": person.created_at.isoformat()
                }],
                ids=[f"person_{person.id}"]
            )
        except Exception as e:
            print(f"Error embedding person {person.id}: {e}")
    
    def embed_commitment(self, commitment: models.Commitment):
        """Add a commitment to the vector store"""
        try:
            # Create text for embedding
            commitment_text = f"Commitment: {commitment.task_description}"
            if commitment.deadline:
                commitment_text += f" Deadline: {commitment.deadline.strftime('%Y-%m-%d')}"
            if hasattr(commitment, 'priority') and commitment.priority:
                commitment_text += f" Priority: {commitment.priority}"
            commitment_text += f" Status: {commitment.status}"
            
            self.commitments_collection.add(
                documents=[commitment_text],
                metadatas=[{
                    "user_id": commitment.user_id,
                    "commitment_id": commitment.id,
                    "task_description": commitment.task_description,
                    "status": commitment.status,
                    "priority": getattr(commitment, 'priority', 'medium'),
                    "deadline": commitment.deadline.isoformat() if commitment.deadline else None,
                    "created_at": commitment.created_at.isoformat()
                }],
                ids=[f"commitment_{commitment.id}"]
            )
        except Exception as e:
            print(f"Error embedding commitment {commitment.id}: {e}")
    
    def search_conversations(
        self,
        query: str,
        user_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar conversations"""
        try:
            results = self.conversations_collection.query(
                query_texts=[query],
                where={"user_id": user_id},
                n_results=limit
            )
            
            if not results['documents'] or not results['documents'][0]:
                return []
            
            formatted_results = []
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i]
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'conversation_id': metadata['conversation_id'],
                    'timestamp': metadata['timestamp'],
                    'user_message': metadata['user_message'],
                    'ai_response': metadata['ai_response']
                })
            
            return formatted_results
        except Exception as e:
            print(f"Error searching conversations: {e}")
            return []
    
    def search_habits(
        self,
        query: str,
        user_id: int,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for similar habits"""
        try:
            results = self.habits_collection.query(
                query_texts=[query],
                where={"user_id": user_id, "is_active": True},
                n_results=limit
            )
            
            if not results['documents'] or not results['documents'][0]:
                return []
            
            formatted_results = []
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i]
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'similarity_score': 1 - results['distances'][0][i],
                    'habit_id': metadata['habit_id'],
                    'name': metadata['name'],
                    'description': metadata['description'],
                    'frequency': metadata['frequency']
                })
            
            return formatted_results
        except Exception as e:
            print(f"Error searching habits: {e}")
            return []
    
    def search_people(
        self,
        query: str,
        user_id: int,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for similar people"""
        try:
            results = self.people_collection.query(
                query_texts=[query],
                where={"user_id": user_id},
                n_results=limit
            )
            
            if not results['documents'] or not results['documents'][0]:
                return []
            
            formatted_results = []
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i]
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'similarity_score': 1 - results['distances'][0][i],
                    'person_id': metadata['person_id'],
                    'name': metadata['name'],
                    'relationship': metadata['relationship'],
                    'pronouns': metadata['pronouns'],
                    'description': metadata['description']
                })
            
            return formatted_results
        except Exception as e:
            print(f"Error searching people: {e}")
            return []
    
    def search_commitments(
        self,
        query: str,
        user_id: int,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for similar commitments"""
        try:
            results = self.commitments_collection.query(
                query_texts=[query],
                where={"user_id": user_id},
                n_results=limit
            )
            
            if not results['documents'] or not results['documents'][0]:
                return []
            
            formatted_results = []
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i]
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'similarity_score': 1 - results['distances'][0][i],
                    'commitment_id': metadata['commitment_id'],
                    'task_description': metadata['task_description'],
                    'status': metadata['status'],
                    'priority': metadata['priority'],
                    'deadline': metadata['deadline']
                })
            
            return formatted_results
        except Exception as e:
            print(f"Error searching commitments: {e}")
            return []
    
    def batch_embed_existing_data(self, db: Session):
        """Embed all existing data from the database"""
        print("Starting batch embedding of existing data...")
        
        # Embed conversations
        conversations = db.query(models.Conversation).all()
        for conv in conversations:
            self.embed_conversation(conv)
        print(f"Embedded {len(conversations)} conversations")
        
        # Embed habits
        habits = db.query(models.Habit).filter(models.Habit.is_active == 1).all()
        for habit in habits:
            self.embed_habit(habit, db)
        print(f"Embedded {len(habits)} active habits")
        
        # Embed people
        people = db.query(models.Person).all()
        for person in people:
            self.embed_person(person)
        print(f"Embedded {len(people)} people")
        
        # Embed commitments
        commitments = db.query(models.Commitment).all()
        for commitment in commitments:
            self.embed_commitment(commitment)
        print(f"Embedded {len(commitments)} commitments")
        
        print("Batch embedding completed!")


# Global instance
vector_store = None

def get_vector_store() -> VectorStore:
    """Get or create global vector store instance"""
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store