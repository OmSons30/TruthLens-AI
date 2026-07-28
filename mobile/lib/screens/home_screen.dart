import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'result_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _customClaimController = TextEditingController();
  bool _isLoading = false;
  bool _isOverlayActive = true;

  final List<Map<String, String>> _samplePosts = [
    {
      "source": "WhatsApp Forwarded",
      "text": "⚠ URGENT: Government giving ₹50,000 subsidy under Direct Relief Scheme to all account holders! Register now at http://bit.ly/fake-subsidy",
      "tag": "Financial Scam"
    },
    {
      "source": "Facebook Post",
      "text": "Breaking: Scientists confirm rare planetary alignment will cause 3 days of total darkness starting tomorrow! Forward to save lives.",
      "tag": "Sensational Claim"
    },
    {
      "source": "Telegram Channel",
      "text": "Official Announcement: Central Bank issuing new ₹500 currency notes with microchip tracking capabilities.",
      "tag": "Fake Announcement"
    }
  ];

  void _analyzeContent(String text, {String source = "WhatsApp"}) async {
    setState(() {
      _isLoading = true;
    });

    try {
      final result = await ApiService.verifyContent(
        rawText: text,
        sourceApp: source,
      );

      if (!mounted) return;

      setState(() {
        _isLoading = false;
      });

      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (context) => ResultScreen(result: result),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Verification failed: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1E293B),
        elevation: 0,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFF3B82F6).withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.shield_rounded, color: Color(0xFF3B82F6), size: 24),
            ),
            const SizedBox(width: 12),
            const Text(
              'TruthLens AI',
              style: TextStyle(
                fontWeight: FontWeight.w800,
                color: Colors.white,
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(
              _isOverlayActive ? Icons.layers_rounded : Icons.layers_clear_rounded,
              color: _isOverlayActive ? const Color(0xFF38BDF8) : Colors.white38,
            ),
            tooltip: 'Toggle Floating Assistant',
            onPressed: () {
              setState(() {
                _isOverlayActive = !_isOverlayActive;
              });
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(_isOverlayActive
                      ? 'Floating Shazam Assistant Active'
                      : 'Floating Shazam Assistant Paused'),
                  duration: const Duration(seconds: 1),
                ),
              );
            },
          )
        ],
      ),
      body: Stack(
        children: [
          SingleChildScrollView(
            physics: const BouncingScrollPhysics(),
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAlignment.start,
              children: [
                // Banner Hero Card
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF2563EB), Color(0xFF1D4ED8)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF2563EB).withOpacity(0.3),
                        blurRadius: 16,
                        offset: const Offset(0, 6),
                      )
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAlignment.start,
                    children: const [
                      Text(
                        'Shazam for Misinformation',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 22,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      SizedBox(height: 8),
                      Text(
                        'One-tap verification shield for WhatsApp, Facebook, Telegram & News claims.',
                        style: TextStyle(
                          color: Color(0xFFDBEAFE),
                          fontSize: 14,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 28),

                // Custom Input Section
                const Text(
                  'Quick Claim Verification',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E293B),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.white10),
                  ),
                  child: Column(
                    children: [
                      TextField(
                        controller: _customClaimController,
                        maxLines: 3,
                        style: const TextStyle(color: Colors.white),
                        decoration: const InputDecoration(
                          hintText: 'Paste a suspicious message, claim, or URL...',
                          hintStyle: TextStyle(color: Colors.white38),
                          border: InputBorder.none,
                        ),
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF0EA5E9),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                          ),
                          onPressed: () {
                            if (_customClaimController.text.trim().isNotEmpty) {
                              _analyzeContent(_customClaimController.text.trim());
                            }
                          },
                          icon: const Icon(Icons.search_rounded, color: Colors.white),
                          label: const Text(
                            'Analyze Content Now',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      )
                    ],
                  ),
                ),
                const SizedBox(height: 28),

                // Simulated Social Feed Tests
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: const [
                    Text(
                      'Sample Forwarded Content',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      'Tap to Scan',
                      style: TextStyle(
                        color: Color(0xFF38BDF8),
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),

                ..._samplePosts.map((post) => Padding(
                      padding: const EdgeInsets.only(bottom: 14.0),
                      child: InkWell(
                        onTap: () => _analyzeContent(post['text']!, source: post['source']!),
                        borderRadius: BorderRadius.circular(18),
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: const Color(0xFF1E293B).withOpacity(0.8),
                            borderRadius: BorderRadius.circular(18),
                            border: Border.all(color: Colors.white.withOpacity(0.08)),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Row(
                                    children: [
                                      const Icon(Icons.mark_chat_unread_rounded,
                                          color: Color(0xFF22C55E), size: 18),
                                      const SizedBox(width: 8),
                                      Text(
                                        post['source']!,
                                        style: const TextStyle(
                                          color: Color(0xFF94A3B8),
                                          fontSize: 13,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ],
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 10, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: Colors.white10,
                                      borderRadius: BorderRadius.circular(20),
                                    ),
                                    child: Text(
                                      post['tag']!,
                                      style: const TextStyle(
                                        color: Colors.white70,
                                        fontSize: 11,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 10),
                              Text(
                                post['text']!,
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 14,
                                  height: 1.4,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    )),
                const SizedBox(height: 80), // Space for floating widget
              ],
            ),
          ),

          // Floating Shazam Scanner Overlay Button Simulation
          if (_isOverlayActive)
            Positioned(
              right: 20,
              bottom: 24,
              child: GestureDetector(
                onTap: () => _analyzeContent(_samplePosts[0]['text']!),
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF0EA5E9), Color(0xFF2563EB)],
                    ),
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF0EA5E9).withOpacity(0.5),
                        blurRadius: 20,
                        spreadRadius: 4,
                      )
                    ],
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: const [
                      Icon(Icons.center_focus_strong_rounded, color: Colors.white, size: 32),
                      SizedBox(height: 4),
                      Text(
                        'SHAZAM',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 9,
                          fontWeight: FontWeight.w900,
                          letterSpacing: 1,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

          // Loading Modal Overlay
          if (_isLoading)
            Container(
              color: Colors.black87,
              child: Center(
                child: Container(
                  padding: const EdgeInsets.all(28),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E293B),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.5)),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: const [
                      SizedBox(
                        width: 50,
                        height: 50,
                        child: CircularProgressIndicator(
                          valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF38BDF8)),
                          strokeWidth: 4,
                        ),
                      ),
                      SizedBox(height: 20),
                      Text(
                        'TruthLens Agent Pipeline Running...',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      SizedBox(height: 6),
                      Text(
                        'OCR -> Claim Extraction -> Fact Checking',
                        style: TextStyle(
                          color: Colors.white54,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
