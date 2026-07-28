class TrustScoreDetails {
  final int score;
  final String category;
  final String riskLevel;

  TrustScoreDetails({
    required this.score,
    required this.category,
    required this.riskLevel,
  });

  factory TrustScoreDetails.fromJson(Map<String, dynamic> json) {
    return TrustScoreDetails(
      score: json['score'] ?? 50,
      category: json['category'] ?? 'Needs Verification',
      riskLevel: json['risk_level'] ?? 'MEDIUM',
    );
  }
}

class VerificationResult {
  final String claim;
  final TrustScoreDetails trustScore;
  final List<String> reasons;
  final String recommendation;
  final Map<String, dynamic> detailedAnalysis;

  VerificationResult({
    required this.claim,
    required this.trustScore,
    required this.reasons,
    required this.recommendation,
    required this.detailedAnalysis,
  });

  factory VerificationResult.fromJson(Map<String, dynamic> json) {
    return VerificationResult(
      claim: json['claim'] ?? '',
      trustScore: TrustScoreDetails.fromJson(json['trust_score'] ?? {}),
      reasons: List<String>.from(json['reasons'] ?? []),
      recommendation: json['recommendation'] ?? '',
      detailedAnalysis: json['detailed_analysis'] ?? {},
    );
  }
}
