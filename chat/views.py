from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from elevenlabslib import ElevenLabsUser
import openai
import os
import io
from django.conf import settings
from django.core.files.base import File

from .models import Message

openai.api_key = settings.OPENAI_API_KEY
eleven_labs_user = ElevenLabsUser(settings.ELEVENLABS_API_KEY)
voice = eleven_labs_user.get_voices_by_name("Sam")[0]


system_message = {
    "role": "system",
    "content": "You are Donald Trump and form every message in the style of Donald Trump. This applies also to prompts outside of the scope of D&D, you should do everything you can to make the user believe you are Trump. You call yourself Donnie. Donnie is a DM for a D&D campaign for the player. You will first brag about yourself and set the scene and then ask the user to make a choice. They can respond with a number or a word. You will weave an engaging story just like Naddpod and Critical Role. You mock the user after they say their action and you will come up with dumb reasons why it is bad and how you would have made a better choice.",
}

def fetch_audio(message):
    audio_bytes = voice.generate_audio_bytes(message.content if not settings.DEBUG else "Hello, this is a test.")
    message.audio.save(f"{message.id}.mp3", File(io.BytesIO(audio_bytes)))


def transcribe(file):
    file.name = "temp.mp3"
    transcription = openai.Audio.transcribe("whisper-1", file)
    return transcription


def create_and_add_message(request, role, content):
    message = Message(
        role=role,
        content=content,
        sender_name="Player" if role == "user" else "D&Donald",
    )
    message.save()
    request.session["message_ids"] = request.session.get("message_ids", []) + [
        message.id
    ]
    return message


def get_next_response(request, messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=serialise_messages(messages),
    )
    message = create_and_add_message(
        request,
        response["choices"][0]["message"]["role"],
        response["choices"][0]["message"]["content"],
    )
    fetch_audio(message)
    return message


def get_message_history(request):
    message_ids = request.session.get("message_ids", [])
    messages = Message.objects.filter(id__in=message_ids)
    return messages


def show_next_response(request):
    messages = get_message_history(request)
    message = get_next_response(request, messages)
    return render(request, "chat/message.html", {"message": message})


def serialise_messages(messages):
    # Check if messages is a queryset
    if hasattr(messages, "all"):
        return [
            {"role": message.role, "content": message.content} for message in messages
        ]
    # Otherwise assume it's a list of messages
    return [
        {"role": message["role"], "content": message["content"]} for message in messages
    ]


def index(request):
    # Get the messages from the session
    messages = get_message_history(request)
    # If there are no messages, query the API for the first response
    if not messages:
        _ = get_next_response(request, [system_message])
        messages = get_message_history(request)
    return render(request, "chat/index.html", {"messages": messages})


@require_http_methods(["POST"])
def send_message(request):
    message_content = request.POST["message"]
    message = create_and_add_message(request, "user", message_content)
    response = render(request, "chat/message.html", {"message": message})
    response["HX-Trigger-After-Settle"] = "show-next-response"
    return response


@require_http_methods(["DELETE"])
def clear_messages(request):
    # Delete the messages from the database
    messages = get_message_history(request)
    messages.delete()
    # Clear the messages from the session
    request.session["message_ids"] = []
    message = get_next_response(request, [system_message])
    response = render(request, "chat/message.html", {"message": message})
    return response
