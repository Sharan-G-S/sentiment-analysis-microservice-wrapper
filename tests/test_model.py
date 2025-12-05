"""
Unit tests for the model wrapper
"""
import pytest
import platform
from app.model import SentimentModel

# Skip model tests on macOS due to PyTorch bus error
skip_on_macos = pytest.mark.skipif(
    platform.system() == "Darwin",
    reason="PyTorch model tests cause bus errors on macOS. Run in Docker instead."
)


@skip_on_macos
@pytest.mark.asyncio
async def test_model_loading():
    """Test model loading and unloading"""
    model = SentimentModel()
    assert not model.is_loaded
    
    await model.load()
    assert model.is_loaded
    
    await model.unload()
    assert not model.is_loaded


@skip_on_macos
@pytest.mark.asyncio
async def test_model_prediction():
    """Test basic prediction"""
    model = SentimentModel()
    await model.load()
    
    result = await model.predict("This is great!")
    
    assert "sentiment" in result
    assert "confidence" in result
    assert result["sentiment"] in ["positive", "negative"]
    assert 0 <= result["confidence"] <= 1
    
    await model.unload()


@skip_on_macos
@pytest.mark.asyncio
async def test_model_prediction_with_probabilities():
    """Test prediction with probability output"""
    model = SentimentModel()
    await model.load()
    
    result = await model.predict("Excellent product!", return_probabilities=True)
    
    assert "probabilities" in result
    assert isinstance(result["probabilities"], dict)
    assert len(result["probabilities"]) > 0
    
    await model.unload()


@skip_on_macos
@pytest.mark.asyncio
async def test_prediction_without_loading():
    """Test that prediction fails when model not loaded"""
    model = SentimentModel()
    
    with pytest.raises(RuntimeError):
        await model.predict("test")


@skip_on_macos
@pytest.mark.asyncio
async def test_model_info():
    """Test model info retrieval"""
    model = SentimentModel()
    await model.load()
    
    info = model.get_info()
    
    assert "model_name" in info
    assert "device" in info
    assert "status" in info
    assert info["status"] == "loaded"
    
    await model.unload()
