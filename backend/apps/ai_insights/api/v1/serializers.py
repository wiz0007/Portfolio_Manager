from rest_framework import serializers


class AIExplainRequestSerializer(serializers.Serializer):
    portfolio_id = serializers.UUIDField(
        required=True,
        help_text="UUID of the portfolio to analyze."
    )
    investment_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Optional UUID of a specific investment holding to focus the explanation on."
    )
    question = serializers.CharField(
        required=True,
        min_length=3,
        max_length=1000,
        help_text="The user's analytical question regarding their portfolio or holding."
    )
    focus_area = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
        default="",
        help_text="Optional focus area (e.g. 'performance', 'allocation', 'risk', 'holdings')."
    )
    as_of_date = serializers.DateField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Optional historical date (YYYY-MM-DD) for point-in-time explanation."
    )


class AIExplanationOutputSerializer(serializers.Serializer):
    answer = serializers.CharField(
        help_text="Plain-language educational explanation grounded strictly in verified portfolio data."
    )
    key_points = serializers.ListField(
        child=serializers.CharField(),
        help_text="Bullet points summarizing core analytical findings."
    )
    limitations = serializers.ListField(
        child=serializers.CharField(),
        help_text="Caveats regarding missing valuations, data completeness, or currency boundaries."
    )
    referenced_metrics = serializers.ListField(
        child=serializers.CharField(),
        help_text="Context metric identifiers explicitly cited in the narrative."
    )
    disclaimer = serializers.CharField(
        help_text="Mandatory regulatory non-advisory disclosure."
    )


class AIUsageSerializer(serializers.Serializer):
    model = serializers.CharField(help_text="OpenAI model identifier used.")
    latency_seconds = serializers.FloatField(help_text="Server-to-OpenAI request round-trip latency.")
    prompt_tokens = serializers.IntegerField(help_text="Tokens consumed by context and prompt.")
    completion_tokens = serializers.IntegerField(help_text="Tokens generated in explanation.")
    total_tokens = serializers.IntegerField(help_text="Total tokens consumed.")
    is_configured = serializers.BooleanField(help_text="Whether OpenAI provider is active.")


class AIExplainResponseSerializer(serializers.Serializer):
    explanation = AIExplanationOutputSerializer(help_text="Structured explanation payload.")
    usage = AIUsageSerializer(help_text="Execution and token usage telemetry.")


class AIStatusResponseSerializer(serializers.Serializer):
    is_configured = serializers.BooleanField(
        help_text="Whether the OpenAI API key is properly configured on the server."
    )
    model = serializers.CharField(
        help_text="Configured OpenAI model identifier."
    )
