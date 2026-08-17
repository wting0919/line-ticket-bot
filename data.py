import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =====================
# 資料處理
# =====================

def load_data():

    try:

        response = (
            supabase
            .table("shows")
            .select("*")
            .execute()
        )

        return response.data or []

    except Exception as e:

        print(
            "讀取 shows 錯誤：",
            repr(e),
            flush=True,
        )

        return []

def update_show(show):

    try:

        show_id = show["id"]

        data = show.copy()
        data.pop("id", None)

        supabase.table("shows") \
            .update(data) \
            .eq("id", show_id) \
            .execute()

    except Exception as e:

        print(
            "更新 show 錯誤：",
            repr(e),
            flush=True,
        )

        raise

def insert_show(show):

    try:

        response = (
            supabase
            .table("shows")
            .insert(show)
            .execute()
        )

        return response.data[0]

    except Exception as e:

        print(
            "新增 show 錯誤：",
            repr(e),
            flush=True,
        )

        raise

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
        print(
            "讀取 members 錯誤：",
            repr(e),
            flush=True,
        )

        return {}

def get_member_user_id(name):

    if not name:
        return None

    members = load_members()
    return members.get(name.strip())


__all__ = [
    "supabase",
    "load_data",
    "update_show",
    "insert_show",
    "get_user_id",
    "get_member",
    "load_members",
    "get_member_user_id",
]

