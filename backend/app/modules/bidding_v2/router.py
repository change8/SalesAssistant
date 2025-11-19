
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.modules.bidding_v2.service import BiddingService
from backend.app.modules.bidding_v2.schemas import BiddingAnalysisResult

router = APIRouter(prefix="/bidding_v2", tags=["bidding_v2"])
service = BiddingService()

@router.post("/analyze", response_model=BiddingAnalysisResult)
async def analyze_bidding_document(file: UploadFile = File(...)):
    try:
        return await service.analyze_document(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
