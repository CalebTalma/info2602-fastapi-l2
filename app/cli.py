import typer
from typing import Annotated # Recommended for modern Typer/FastAPI style
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from sqlmodel import select, or_
from sqlalchemy.exc import IntegrityError

cli = typer.Typer(help="User Management Database CLI")

@cli.command()
def initialize():
    """
    Wipe the database and seed it with a default 'bob' user.
    WARNING: This drops all existing data.
    """
    with get_session() as db:
        drop_all() 
        create_db_and_tables() 
        bob = User(username='bob', email='bob@mail.com', password='bobpass') 
        db.add(bob) 
        db.commit() 
        db.refresh(bob) 
        print("Database Initialized")

@cli.command()
def get_user(
    username: Annotated[str, typer.Argument(help="The exact username to search for")]
):
    """Retrieve a single user's details by their username."""
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'Error: {username} not found!')
            return
        print(user)

@cli.command()
def get_all_users():
    """List every user currently registered in the database."""
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)

@cli.command()
def change_email(
    username: Annotated[str, typer.Argument(help="Username of the account to update")],
    new_email: Annotated[str, typer.Argument(help="The new email address to assign")]
):
    """Update the email address for an existing user."""
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'Error: {username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Success: Updated {user.username}'s email to {user.email}")

@cli.command()
def create_user(
    username: Annotated[str, typer.Argument(help="Unique username for the new account")],
    email: Annotated[str, typer.Argument(help="Unique email address")],
    password: Annotated[str, typer.Argument(help="User password (plain text for this exercise)")]
):
    """Register a new user in the system."""
    with get_session() as db:
        newuser = User(username=username, email=email, password=password)
        try:
            db.add(newuser)
            db.commit()
            db.refresh(newuser)
        except IntegrityError:
            db.rollback()
            print("Error: Username or email already taken!")
        else:
            print(f"Created: {newuser}")

@cli.command()
def delete_user(
    username: Annotated[str, typer.Argument(help="The username to permanently remove")]
):
    """Remove a user from the database."""
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'Error: {username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'Success: {username} deleted')

@cli.command()
def search_users(
    query: Annotated[str, typer.Argument(help="Partial string to match against username or email")]
):
    """Find users using a partial match on username or email (Case-sensitive)."""
    with get_session() as db:
        statement = select(User).where(
            or_(
                User.username.contains(query),
                User.email.contains(query)
            )
        )
        results = db.exec(statement).all()
        if not results:
            print(f"No matches found for: {query}")
        else:
            for user in results:
                print(user)

@cli.command()
def list_paginated(
    limit: Annotated[int, typer.Option(help="Maximum number of users to return")] = 10,
    offset: Annotated[int, typer.Option(help="Number of users to skip from the start")] = 0
):
    """
    List users using pagination (limit and offset). 
    Useful for large datasets to avoid loading everything at once.
    """
    with get_session() as db:
        statement = select(User).offset(offset).limit(limit)
        results = db.exec(statement).all()
        if not results:
            print("No users found in this range.")
        else:
            print(f"--- Results (Limit: {limit}, Offset: {offset}) ---")
            for user in results:
                print(user)

if __name__ == "__main__":
    cli()