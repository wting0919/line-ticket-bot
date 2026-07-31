import os
import json

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

USER_FILE = "./users.json"


# =====================
# 資料處理
# =====================

def load_data():

    response = (
        supabase
        .table("shows")
        .select("*")
        .execute()
    )

    shows = response.data

    return shows

def save_data(data):

    try:

        if data:

            supabase.table("shows").upsert(
                data
            ).execute()


        print("Supabase儲存完成")


    except Exception as e:

        print("Supabase儲存錯誤：", e)

def update_show(show):

    show_id = show["id"]

    data = show.copy()
    data.pop("id")

    supabase.table("shows") \
        .update(data) \
        .eq("id", show_id) \
        .execute()

def insert_show(show):

    response = (
        supabase
        .table("shows")
        .insert(show)
        .execute()
    )

    return response.data[0]

def get_user_id(name):
    result = (
        supabase
        .table("members")
        .select("user_id")
        .eq("name", name)
        .execute()
    )

    if result.data:
        return result.data[0]["user_id"]

    return None

def get_member(name):
    result = (
        supabase
        .table("members")
        .select("*")
        .eq("name", name)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None

def load_members():

    try:
        response = (
            supabase
            .table("members")
            .select("*")
            .execute()
        )

        return {
            row["name"].strip(): row["user_id"].strip()
            for row in response.data
            if row.get("name") and row.get("user_id")
        }

    except Exception as e:
        print("讀取 members 錯誤：", e)
        return {}

def get_member_user_id(name):

    if not name:
        return None

    members = load_members()
    return members.get(name.strip())


__all__ = [
    "supabase",
    "load_data",
    "save_data",
    "update_show",
    "insert_show",
    "get_user_id",
    "get_member",
    "load_members",
    "get_member_user_id",
]

