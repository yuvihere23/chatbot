# app/routes/network.py
from fastapi import APIRouter
from app.services.network import list_vnets, list_subnets

router = APIRouter()

@router.get("/vnets")
def get_vnets():
    return {"vnets": list_vnets()}

@router.get("/subnets")
def get_subnets():
    return {"subnets": list_subnets()}
