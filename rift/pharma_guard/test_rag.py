"""
Test RAG integration with LLM
"""

from llm import get_explanation
from rag_retrieval import GuidelineRetriever

def test_rag():
    """Test the complete RAG pipeline"""
    
    print("🧪 Testing RAG Integration\n")
    
    # Test database first
    retriever = GuidelineRetriever()
    guideline = retriever.get_guideline("CODEINE", "PM")
    
    if guideline:
        print("✅ Database working")
        print(f"   Found: {guideline['drug_name']} - {guideline['phenotype_name']}")
    else:
        print("❌ Database not working")
        return
    
    # Test with real drug/phenotype
    print("\n🤖 Testing LLM with RAG...")
    result = get_explanation("CODEINE", "PM", [])
    
    if result and "summary" in result:
        print("\n✅ LLM Response:")
        print(f"   Summary: {result['summary']}")
        print(f"   Mechanism: {result['mechanism'][:100]}...")
        if "citations" in result:
            print(f"   Citations: {result['citations']}")
    else:
        print("❌ LLM failed")

if __name__ == "__main__":
    test_rag()