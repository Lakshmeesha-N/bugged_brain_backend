from typing import Optional
from pydantic import BaseModel, Field


class Project(BaseModel):
    title: str
    description: str
    tech_stack: list[str] = Field(default_factory=list)
    link: Optional[str] = None


class Experience(BaseModel):
    company: str
    role: str
    duration: str
    description: str


class Education(BaseModel):
    institution: str
    degree: str
    year: str
    grade: Optional[str] = None


class Achievement(BaseModel):
    title: str
    description: Optional[str] = None
    year: Optional[str] = None


class Certification(BaseModel):
    name: str
    issuer: Optional[str] = None
    year: Optional[str] = None


class Publication(BaseModel):
    title: str
    venue: Optional[str] = None
    year: Optional[str] = None
    link: Optional[str] = None


class Extracurricular(BaseModel):
    title: str
    role: Optional[str] = None
    description: Optional[str] = None


class Links(BaseModel):
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: Optional[str] = None


class ProfileSchema(BaseModel):
    # Required
    name: str
    email: str
    education: list[Education] = Field(..., min_length=1)

    # Optional
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    links: Optional[Links] = None
    skills: list[str] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    achievements: list[Achievement] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    publications: list[Publication] = Field(default_factory=list)
    extracurriculars: list[Extracurricular] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
