from __future__ import annotations

from django.http import HttpResponse

from django_integrity_policy.decorators import (
    integrity_policy_override,
    integrity_policy_report_only_override,
)


def index(request):
    return HttpResponse("Hello World")


async def async_index(request):
    return HttpResponse("Hello World")


@integrity_policy_override({"blocked-destinations": ["script"]})
def override_index(request):
    return HttpResponse("Hello World")


@integrity_policy_override({})
def override_disabled_index(request):
    return HttpResponse("Hello World")


@integrity_policy_report_only_override({"blocked-destinations": ["script"]})
def report_only_override_index(request):
    return HttpResponse("Hello World")


@integrity_policy_report_only_override({})
def report_only_override_disabled_index(request):
    return HttpResponse("Hello World")


@integrity_policy_override({"blocked-destinations": ["script"]})
async def async_override_index(request):
    return HttpResponse("Hello World")


@integrity_policy_override({})
async def async_override_disabled_index(request):
    return HttpResponse("Hello World")


@integrity_policy_report_only_override({"blocked-destinations": ["script"]})
async def async_report_only_override_index(request):
    return HttpResponse("Hello World")


@integrity_policy_report_only_override({})
async def async_report_only_override_disabled_index(request):
    return HttpResponse("Hello World")
