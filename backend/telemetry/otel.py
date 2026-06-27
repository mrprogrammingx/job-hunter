"""
OpenTelemetry setup.

When OTEL_ENABLED=true, spans are exported to an OTLP collector (e.g. Jaeger,
Tempo, Honeycomb) at OTEL_ENDPOINT. Otherwise a console exporter is used so
you can see traces in the terminal during development without any collector.
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME


_provider: TracerProvider | None = None


def setup_telemetry(service_name: str = "job-hunter", otel_enabled: bool = False, endpoint: str = "") -> None:
    global _provider

    resource = Resource.create({SERVICE_NAME: service_name})
    _provider = TracerProvider(resource=resource)

    if otel_enabled and endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        except Exception:
            exporter = ConsoleSpanExporter()
    else:
        exporter = ConsoleSpanExporter()

    _provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(_provider)


def get_tracer(name: str = "job-hunter.agents") -> trace.Tracer:
    return trace.get_tracer(name)
