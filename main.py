"""
FastAPI Application for Legal Document Analysis
Provides endpoints for uploading documents and performing AI-powered legal analysis
using OpenAI integration for contracts, compliance, IP, corporate, labor, and tax analysis.
"""

import os
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import PyPDF2
import docx

# Initialize FastAPI app
app = FastAPI(
    title="Legal Document Analyzer",
    description="AI-powered legal document analysis platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

RESULTS_DIR = Path("analysis_results")
RESULTS_DIR.mkdir(exist_ok=True)


# ==================== Pydantic Models ====================

class AnalysisRequest(BaseModel):
    """Request model for analysis endpoints"""
    analysis_type: str
    focus_areas: Optional[List[str]] = None
    language: str = "English"


class ContractAnalysisRequest(AnalysisRequest):
    """Contract-specific analysis request"""
    analysis_type: str = "contract"
    focus_areas: Optional[List[str]] = ["terms", "liability", "payment", "termination"]


class ComplianceAnalysisRequest(AnalysisRequest):
    """Compliance analysis request"""
    analysis_type: str = "compliance"
    focus_areas: Optional[List[str]] = ["regulations", "standards", "requirements"]


class IPAnalysisRequest(AnalysisRequest):
    """Intellectual Property analysis request"""
    analysis_type: str = "ip"
    focus_areas: Optional[List[str]] = ["patents", "trademarks", "copyrights", "licensing"]


class CorporateAnalysisRequest(AnalysisRequest):
    """Corporate governance analysis request"""
    analysis_type: str = "corporate"
    focus_areas: Optional[List[str]] = ["governance", "ownership", "structure", "compliance"]


class LaborAnalysisRequest(AnalysisRequest):
    """Labor law analysis request"""
    analysis_type: str = "labor"
    focus_areas: Optional[List[str]] = ["employment", "benefits", "disputes", "regulations"]


class TaxAnalysisRequest(AnalysisRequest):
    """Tax analysis request"""
    analysis_type: str = "tax"
    focus_areas: Optional[List[str]] = ["deductions", "credits", "liabilities", "planning"]


class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    document_id: str
    analysis_type: str
    status: str
    timestamp: str
    summary: Optional[str] = None
    key_findings: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    detailed_analysis: Optional[dict] = None


class DocumentMetadata(BaseModel):
    """Document metadata"""
    document_id: str
    filename: str
    file_type: str
    upload_time: str
    file_size: int
    status: str


# ==================== Utility Functions ====================

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading DOCX: {str(e)}")


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading TXT: {str(e)}")


def extract_document_text(file_path: str, file_type: str) -> str:
    """Extract text based on file type"""
    if file_type.lower() == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type.lower() in ["docx", "doc"]:
        return extract_text_from_docx(file_path)
    elif file_type.lower() == "txt":
        return extract_text_from_txt(file_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")


def call_openai_api(prompt: str, model: str = "gpt-4") -> str:
    """Call OpenAI API for analysis"""
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert legal analyst with deep knowledge across contracts, compliance, intellectual property, corporate governance, labor law, and tax law."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")


def generate_analysis_prompt(analysis_type: str, document_text: str, focus_areas: List[str]) -> str:
    """Generate analysis prompt based on type"""
    base_prompt = f"""Analyze the following legal document with focus on {analysis_type} aspects.
Focus areas: {', '.join(focus_areas)}

Document text:
{document_text[:5000]}

Please provide:
1. Executive Summary (2-3 sentences)
2. Key Findings (5-7 bullet points)
3. Risk Assessment (identify major risks)
4. Recommendations (actionable recommendations)
5. Detailed Analysis by focus area

Format your response as JSON with keys: summary, key_findings, risks, recommendations, detailed_analysis"""
    return base_prompt


def save_analysis_result(document_id: str, analysis_data: dict) -> str:
    """Save analysis result to file"""
    try:
        result_file = RESULTS_DIR / f"{document_id}_analysis.json"
        with open(result_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        return str(result_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving analysis: {str(e)}")


# ==================== Health Check ====================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - Health check"""
    return {
        "status": "healthy",
        "service": "Legal Document Analyzer",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "openai_configured": bool(openai.api_key)
    }


# ==================== Document Upload ====================

@app.post("/api/v1/upload", tags=["Document Upload"], response_model=DocumentMetadata)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a legal document for analysis
    
    Supported formats: PDF, DOCX, TXT
    """
    try:
        # Validate file type
        allowed_types = {".pdf", ".docx", ".doc", ".txt"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Generate document ID
        document_id = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename.split('.')[0]}"
        
        # Save file
        file_path = UPLOAD_DIR / f"{document_id}{file_ext}"
        content = await file.read()
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return DocumentMetadata(
            document_id=document_id,
            filename=file.filename,
            file_type=file_ext[1:],  # Remove the dot
            upload_time=datetime.utcnow().isoformat(),
            file_size=len(content),
            status="uploaded"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ==================== Contract Analysis ====================

@app.post("/api/v1/analyze/contract", tags=["Contract Analysis"], response_model=AnalysisResponse)
async def analyze_contract(
    document_id: str,
    file_type: str,
    request: ContractAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze a contract document
    
    Examines:
    - Contract terms and conditions
    - Liability clauses
    - Payment terms
    - Termination conditions
    - Risk assessment
    """
    try:
        # Find the document
        file_path = next(UPLOAD_DIR.glob(f"{document_id}.*"), None)
        if not file_path:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Extract text
        document_text = extract_document_text(str(file_path), file_type)
        
        # Generate analysis prompt
        focus_areas = request.focus_areas or ["terms", "liability", "payment", "termination"]
        prompt = generate_analysis_prompt("contract", document_text, focus_areas)
        
        # Call OpenAI
        analysis_result = call_openai_api(prompt)
        
        # Parse response
        try:
            analysis_data = json.loads(analysis_result)
        except json.JSONDecodeError:
            analysis_data = {
                "summary": analysis_result[:200],
                "detailed_analysis": {"raw_response": analysis_result}
            }
        
        response = AnalysisResponse(
            document_id=document_id,
            analysis_type="contract",
            status="completed",
            timestamp=datetime.utcnow().isoformat(),
            summary=analysis_data.get("summary"),
            key_findings=analysis_data.get("key_findings", []),
            risks=analysis_data.get("risks", []),
            recommendations=analysis_data.get("recommendations", []),
            detailed_analysis=analysis_data.get("detailed_analysis", {})
        )
        
        # Save results in background
        background_tasks.add_task(save_analysis_result, document_id, response.dict())
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contract analysis failed: {str(e)}")


# ==================== Compliance Analysis ====================

@app.post("/api/v1/analyze/compliance", tags=["Compliance Analysis"], response_model=AnalysisResponse)
async def analyze_compliance(
    document_id: str,
    file_type: str,
    request: ComplianceAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze document compliance
    
    Examines:
    - Regulatory requirements
    - Industry standards
    - Compliance gaps
    - Risk assessment
    """
    try:
        file_path = next(UPLOAD_DIR.glob(f"{document_id}.*"), None)
        if not file_path:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document_text = extract_document_text(str(file_path), file_type)
        
        focus_areas = request.focus_areas or ["regulations", "standards", "requirements"]
        prompt = generate_analysis_prompt("compliance", document_text, focus_areas)
        
        analysis_result = call_openai_api(prompt)
        
        try:
            analysis_data = json.loads(analysis_result)
        except json.JSONDecodeError:
            analysis_data = {
                "summary": analysis_result[:200],
                "detailed_analysis": {"raw_response": analysis_result}
            }
        
        response = AnalysisResponse(
            document_id=document_id,
            analysis_type="compliance",
            status="completed",
            timestamp=datetime.utcnow().isoformat(),
            summary=analysis_data.get("summary"),
            key_findings=analysis_data.get("key_findings", []),
            risks=analysis_data.get("risks", []),
            recommendations=analysis_data.get("recommendations", []),
            detailed_analysis=analysis_data.get("detailed_analysis", {})
        )
        
        background_tasks.add_task(save_analysis_result, document_id, response.dict())
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance analysis failed: {str(e)}")


# ==================== IP Analysis ====================

@app.post("/api/v1/analyze/ip", tags=["IP Analysis"], response_model=AnalysisResponse)
async def analyze_ip(
    document_id: str,
    file_type: str,
    request: IPAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze intellectual property aspects
    
    Examines:
    - Patent claims and protection
    - Trademark issues
    - Copyright compliance
    - Licensing agreements
    """
    try:
        file_path = next(UPLOAD_DIR.glob(f"{document_id}.*"), None)
        if not file_path:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document_text = extract_document_text(str(file_path), file_type)
        
        focus_areas = request.focus_areas or ["patents", "trademarks", "copyrights", "licensing"]
        prompt = generate_analysis_prompt("intellectual property", document_text, focus_areas)
        
        analysis_result = call_openai_api(prompt)
        
        try:
            analysis_data = json.loads(analysis_result)
        except json.JSONDecodeError:
            analysis_data = {
                "summary": analysis_result[:200],
                "detailed_analysis": {"raw_response": analysis_result}
            }
        
        response = AnalysisResponse(
            document_id=document_id,
            analysis_type="ip",
            status="completed",
            timestamp=datetime.utcnow().isoformat(),
            summary=analysis_data.get("summary"),
            key_findings=analysis_data.get("key_findings", []),
            risks=analysis_data.get("risks", []),
            recommendations=analysis_data.get("recommendations", []),
            detailed_analysis=analysis_data.get("detailed_analysis", {})
        )
        
        background_tasks.add_task(save_analysis_result, document_id, response.dict())
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IP analysis failed: {str(e)}")


# ==================== Corporate Analysis ====================

@app.post("/api/v1/analyze/corporate", tags=["Corporate Analysis"], response_model=AnalysisResponse)
async def analyze_corporate(
    document_id: str,
    file_type: str,
    request: CorporateAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze corporate governance aspects
    
    Examines:
    - Corporate structure
    - Governance compliance
    - Ownership issues
    - Regulatory compliance
    """
    try:
        file_path = next(UPLOAD_DIR.glob(f"{document_id}.*"), None)
        if not file_path:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document_text = extract_document_text(str(file_path), file_type)
        
        focus_areas = request.focus_areas or ["governance", "ownership", "structure", "compliance"]
        prompt = generate_analysis_prompt("corporate governance", document_text, focus_areas)
        
        analysis_result = call_openai_api(prompt)
        
        try:
            analysis_data = json.loads(analysis_result)
        except json.JSONDecodeError:
            analysis_data = {
                "summary": analysis_result[:200],
                "detailed_analysis": {"raw_response": analysis_result}
            }
        
        response = AnalysisResponse(
            document_id=document_id,
            analysis_type="corporate",
            status="completed",
            timestamp=datetime.utcnow().isoformat(),
            summary=analysis_data.get("summary"),
            key_findings=analysis_data.get("key_findings", []),
            risks=analysis_data.get("risks", []),
            recommendations=analysis_data.get("recommendations", []),
            detailed_analysis=analysis_data.get("detailed_analysis", {})
        )
        
        background_tasks.add_task(save_analysis_result, document_id, response.dict())
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Corporate analysis failed: {str(e)}")


# ==================== Labor Analysis ====================

@app.post("/api/v1/analyze/labor", tags=["Labor Analysis"], response_model=AnalysisResponse)
async def analyze_labor(
    document_id: str,
    file_type: str,
    request: LaborAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze labor law aspects
    
    Examines:
    - Employment terms
    - Benefits and compensation
    - Dispute resolution
    - Labor law compliance
    """
    try:
        file_path = next(UPLOAD_DIR.glob(f"{document_id}.*"), None)
        if not file_path:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document_text = extract_document_text(str(file_path), file_type)
        
        focus_areas = request.focus_areas or ["employment", "benefits", "disputes", "regulations"]
        prompt = generate_analysis_prompt("labor law", document_text, focus_areas)
        
        analysis_result = call_openai_api(prompt)
        
        try:
            analysis_data = json.loads(analysis_result)
        except json.JSONDecodeError:
            analysis_data = {
                "summary": analysis_result[:200],
                "detailed_analysis": {"raw_response": analysis_result}
            }
        
        response = AnalysisResponse(
            document_id=document_id,
            analysis_type="labor",
            status="completed",
            timestamp=datetime.utcnow().isoformat(),
            summary=analysis_data.get("summary"),
            key_findings=analysis_data.get("key_findings", []),
            risks=analysis_data.get("risks", []),
            recommendations=analysis_data.get("recommendations", []),
            detailed_analysis=analysis_data.get("detailed_analysis", {})
        )
        
        background_tasks.add_task(save_analysis_result, document_id, response.dict())
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Labor analysis failed: {str(e)}")


# ==================== Tax Analysis ====================

@app.post("/api/v1/analyze/tax", tags=["Tax Analysis"], response_model=AnalysisResponse)
async def analyze_tax(
    document_id: str,
    file_type: str,
    request: TaxAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze tax implications
    
    Examines:
    - Tax deductions and credits
    - Tax liabilities
    - Tax planning opportunities
    - Compliance issues
    """
    try:
        file_path = next(UPLOAD_DIR.glob(f"{document_id}.*"), None)
        if not file_path:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document_text = extract_document_text(str(file_path), file_type)
        
        focus_areas = request.focus_areas or ["deductions", "credits", "liabilities", "planning"]
        prompt = generate_analysis_prompt("tax law", document_text, focus_areas)
        
        analysis_result = call_openai_api(prompt)
        
        try:
            analysis_data = json.loads(analysis_result)
        except json.JSONDecodeError:
            analysis_data = {
                "summary": analysis_result[:200],
                "detailed_analysis": {"raw_response": analysis_result}
            }
        
        response = AnalysisResponse(
            document_id=document_id,
            analysis_type="tax",
            status="completed",
            timestamp=datetime.utcnow().isoformat(),
            summary=analysis_data.get("summary"),
            key_findings=analysis_data.get("key_findings", []),
            risks=analysis_data.get("risks", []),
            recommendations=analysis_data.get("recommendations", []),
            detailed_analysis=analysis_data.get("detailed_analysis", {})
        )
        
        background_tasks.add_task(save_analysis_result, document_id, response.dict())
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tax analysis failed: {str(e)}")


# ==================== Batch Analysis ====================

@app.post("/api/v1/analyze/batch", tags=["Batch Analysis"])
async def batch_analysis(
    document_id: str,
    file_type: str,
    analysis_types: List[str],
    background_tasks: BackgroundTasks
):
    """
    Perform multiple analyses on a single document
    
    Supported analysis types: contract, compliance, ip, corporate, labor, tax
    """
    try:
        file_path = next(UPLOAD_DIR.glob(f"{document_id}.*"), None)
        if not file_path:
            raise HTTPException(status_code=404, detail="Document not found")
        
        valid_types = {"contract", "compliance", "ip", "corporate", "labor", "tax"}
        invalid_types = set(analysis_types) - valid_types
        
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis types: {', '.join(invalid_types)}"
            )
        
        document_text = extract_document_text(str(file_path), file_type)
        
        results = {}
        for analysis_type in analysis_types:
            focus_areas_map = {
                "contract": ["terms", "liability", "payment", "termination"],
                "compliance": ["regulations", "standards", "requirements"],
                "ip": ["patents", "trademarks", "copyrights", "licensing"],
                "corporate": ["governance", "ownership", "structure", "compliance"],
                "labor": ["employment", "benefits", "disputes", "regulations"],
                "tax": ["deductions", "credits", "liabilities", "planning"]
            }
            
            prompt = generate_analysis_prompt(analysis_type, document_text, focus_areas_map[analysis_type])
            analysis_result = call_openai_api(prompt)
            
            try:
                results[analysis_type] = json.loads(analysis_result)
            except json.JSONDecodeError:
                results[analysis_type] = {
                    "summary": analysis_result[:200],
                    "detailed_analysis": {"raw_response": analysis_result}
                }
        
        response_data = {
            "document_id": document_id,
            "analysis_type": "batch",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "analyses": results,
            "analysis_count": len(analysis_types)
        }
        
        background_tasks.add_task(save_analysis_result, f"{document_id}_batch", response_data)
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


# ==================== Results Retrieval ====================

@app.get("/api/v1/results/{document_id}", tags=["Results"])
async def get_analysis_results(document_id: str):
    """
    Retrieve analysis results for a document
    """
    try:
        result_file = RESULTS_DIR / f"{document_id}_analysis.json"
        
        if not result_file.exists():
            raise HTTPException(status_code=404, detail="Analysis results not found")
        
        with open(result_file, 'r') as f:
            results = json.load(f)
        
        return results
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving results: {str(e)}")


@app.get("/api/v1/results/{document_id}/download", tags=["Results"])
async def download_analysis_results(document_id: str):
    """
    Download analysis results as JSON file
    """
    try:
        result_file = RESULTS_DIR / f"{document_id}_analysis.json"
        
        if not result_file.exists():
            raise HTTPException(status_code=404, detail="Analysis results not found")
        
        return FileResponse(
            path=result_file,
            filename=f"{document_id}_analysis.json",
            media_type="application/json"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading results: {str(e)}")


# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ==================== Startup and Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("Legal Document Analyzer started")
    print(f"OpenAI API configured: {bool(openai.api_key)}")
    print(f"Upload directory: {UPLOAD_DIR.absolute()}")
    print(f"Results directory: {RESULTS_DIR.absolute()}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Legal Document Analyzer shutdown")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
