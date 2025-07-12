from flask import Flask, request, jsonify
import openai
import os
from typing import Dict, Any
import json
from dotenv import load_dotenv
load_dotenv()
from vapi import Vapi
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Vapi configuration
VAPI_TOKEN = os.getenv('VAPI_TOKEN')

vapi_client = Vapi(token=VAPI_TOKEN)

class InterviewAnalyzer:
    def __init__(self):
        self.evaluation_criteria = [
            "Problem structuring and framework development",
            "Quantitative analysis and comfort with numbers", 
            "Business judgment and practical insights",
            "Communication clarity and logical flow",
            "Creativity in solution development"
        ]
    
    def get_transcript_from_vapi(self, call_id: str) -> str:
        """
        Fetch transcript from Vapi using call ID
        """
        try:
            call_details = vapi_client.calls.get(id=call_id)
            transcript = call_details.artifact.transcript
            return transcript
        except Exception as e:
            raise Exception(f"Failed to fetch transcript from Vapi: {str(e)}")
    
    def analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze interview transcript using OpenAI API
        """


        sys_prompt = """You are a highly experienced interview evaluator who has assessed over 1,000 business case interviews across consulting, tech, and private equity. You have deep expertise in identifying candidate behaviors and competencies that correlate with success at top firms (e.g., MBB, FAANG). Your task is to provide an in-depth, constructive, and structured evaluation of the candidate’s performance.

    Analyze the following interview transcript and evaluate the candidate across the following five parameters:

        1. Problem structuring and framework development  
        2. Quantitative analysis and comfort with numbers  
        3. Business judgment and practical insights  
        4. Communication clarity and logical flow  
        5. Creativity in solution development

    For each parameter, provide:
    - A score from 1 to 10, where:  
        - 10 = Exceptional (top 1% of candidates)  
        - 7 = Strong but with room for improvement  
        - 4 = Below bar  
        - 1 = Severely lacking
    - Detailed feedback (at least 3–5 sentences), grounded in specific moments from the transcript
    - Strengths demonstrated
    - Areas for improvement

    Also include:
    - An `"overall_score"` (average of the five individual scores)
    - A `"summary"` that synthesizes the candidate’s performance across all parameters, clearly stating whether you would recommend moving forward (yes/no/maybe)
    - A `"red_flags"` field (optional) to highlight any major concerns such as unethical thinking, communication breakdowns, or critical analytical errors

    Please format your response as a JSON object with the following structure:
        {{
            "overall_score": <average score>,
            "detailed_feedback": {{
                "problem_structuring": {{
                    "score": <score>,
                    "feedback": "<detailed feedback>",
                    "strengths": "<strengths>",
                    "improvements": "<areas for improvement>"
                }},
                "quantitative_analysis": {{
                    "score": <score>,
                    "feedback": "<detailed feedback>",
                    "strengths": "<strengths>",
                    "improvements": "<areas for improvement>"
                }},
                "business_judgment": {{
                    "score": <score>,
                    "feedback": "<detailed feedback>",
                    "strengths": "<strengths>",
                    "improvements": "<areas for improvement>"
                }},
                "communication_clarity": {{
                    "score": <score>,
                    "feedback": "<detailed feedback>",
                    "strengths": "<strengths>",
                    "improvements": "<areas for improvement>"
                }},
                "creativity": {{
                    "score": <score>,
                    "feedback": "<detailed feedback>",
                    "strengths": "<strengths>",
                    "improvements": "<areas for improvement>"
                }}
            }},
            "summary": "<overall summary of the interview performance>"
        }}"""

        prompt = f"""Interview Transcript:
        {transcript}"""
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            try:
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                json_str = content[start_idx:end_idx]
                analysis_result = json.loads(json_str)
                return analysis_result
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse AI response",
                    "raw_response": content
                }
                
        except Exception as e:
            return {
                "error": f"OpenAI API error: {str(e)}"
            }

# Initialize analyzer
analyzer = InterviewAnalyzer()

@app.route('/analyze-call/<call_id>', methods=['GET'])
def analyze_by_call_id(call_id: str):
    """
    Convenient GET endpoint to analyze by call ID directly
    """
    try:
        transcript = analyzer.get_transcript_from_vapi(call_id)
        analysis_result = analyzer.analyze_transcript(transcript)
        
        return jsonify({
            "success": True,
            "call_id": call_id,
            "analysis": analysis_result,
            "transcript_length": len(transcript)
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Error analyzing call {call_id}: {str(e)}"
        }), 500

@app.route('/get-transcript/<call_id>', methods=['GET'])
def get_transcript_only(call_id: str):
    """
    Endpoint to just fetch transcript without analysis
    """
    try:
        transcript = analyzer.get_transcript_from_vapi(call_id)
        
        return jsonify({
            "success": True,
            "call_id": call_id,
            "transcript": transcript,
            "transcript_length": len(transcript)
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Error fetching transcript for call {call_id}: {str(e)}"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API documentation"""
    return jsonify({
        "message": "Interview Transcript Analysis API",
        "endpoints": {
            "/analyze-call/<call_id>": "GET - Analyze by call ID directly",
            "/get-transcript/<call_id>": "GET - Get transcript only",
            "/health": "GET - Health check"
        },
        "usage_examples": {
            "analyze_with_transcript": {
                "method": "POST",
                "url": "/analyze",
                "body": {"transcript": "Your interview transcript here..."}
            },
            "analyze_with_call_id": {
                "method": "POST", 
                "url": "/analyze",
                "body": {"call_id": "your-vapi-call-id"}
            },
            "direct_analysis": {
                "method": "GET",
                "url": "/analyze-call/39721b13-a0ef-48a8-baa0-d7c5a96d08c5"
            }
        }
    })

# Convenience function for direct usage
def analyze_call_directly(call_id: str = "39721b13-a0ef-48a8-baa0-d7c5a96d08c5"):
    """
    Direct function to analyze a call - useful for testing
    """
    try:
        transcript = analyzer.get_transcript_from_vapi(call_id)
        print(f"Transcript fetched (length: {len(transcript)} characters)")
        print("-" * 50)
        
        analysis = analyzer.analyze_transcript(transcript)
        print("Analysis completed!")
        print(json.dumps(analysis, indent=2))
        return analysis
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
