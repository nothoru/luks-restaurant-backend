# backend/analytics/management/commands/generate_recommendation.py

import os
import shutil
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
import google.generativeai as genai
from dotenv import load_dotenv

from analytics.models import Analytics

load_dotenv(os.path.join(settings.BASE_DIR, '.env'))
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")
genai.configure(api_key=GOOGLE_API_KEY)


class Command(BaseCommand):
    help = 'Generates a weekly business recommendation using RAG and saves it to the Analytics table.'

    def handle(self, *args, **options):
        self.stdout.write("--- Starting Weekly Recommendation Generation ---")

        # Initialize Vector Store 
        KNOWLEDGE_BASE_FILE_PATH = os.path.join(settings.BASE_DIR, 'analytics', 'data', 'knowledge_base.txt')
        CHROMA_PATH = os.path.join(settings.BASE_DIR, 'chroma_db')
        
        vectorstore = self.initialize_vector_store(KNOWLEDGE_BASE_FILE_PATH, CHROMA_PATH)
        if not vectorstore:
            self.stdout.write(self.style.ERROR("Exiting: Vector store initialization failed."))
            return

        # Fetch Data 
        try:
            # Fetch the latest weekly report that has no recommendation
            latest_report = Analytics.objects.filter(report_type='weekly', recommendation__isnull=True).order_by('-start_date').first()
            if not latest_report:
                self.stdout.write(self.style.WARNING("No new weekly reports found needing a recommendation."))
                return

            # Fetch the previous week's report to get its recommendation and status
            previous_report = Analytics.objects.filter(report_type='weekly', start_date__lt=latest_report.start_date).order_by('-start_date').first()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching data from PostgreSQL: {e}"))
            return
            
        self.stdout.write(f"Successfully fetched KPIs for Week: {latest_report.start_date} to {latest_report.end_date}")
        
        kpi_text, kpi_raw, slow_hours = self.format_kpi_text(latest_report)
        last_week_reco = previous_report.recommendation if previous_report else "N/A (First week of data)"
        last_week_status_text = previous_report.get_recommendation_status_display() if previous_report else "N/A"

        #  RAG Retrieval 
        base_query = self.generate_kb_query_from_kpis(kpi_raw, slow_hours)
        multi_queries = [
            base_query,
            "actionable advice for restaurant menu optimization based on sales data",
            "strategies to improve customer traffic patterns in a restaurant"
        ]
        all_docs = []
        for q in multi_queries:
            docs = vectorstore.similarity_search(q, k=2)
            all_docs.extend(docs)
        unique_docs = list({doc.page_content: doc for doc in all_docs}.values())
        context = "\n\n---\n\n".join(doc.page_content for doc in unique_docs)
        self.stdout.write(f"Retrieved {len(unique_docs)} unique documents from knowledge base.")

        #  Final System Prompt 
        system_prompt = self.build_system_prompt(kpi_text, last_week_reco, last_week_status_text, context, latest_report)
        self.stdout.write("Final prompt for LLM has been built.")

        # Final Recommendation 
        self.stdout.write("Generating new recommendation from Gemini...")
        recommendation = self.generate_recommendation_from_llm(system_prompt)
        
        if not recommendation:
            self.stdout.write(self.style.ERROR("Exiting: Failed to generate recommendation from the AI model."))
            return

        self.stdout.write(self.style.SUCCESS("\n" + "="*20 + " ✅ FINAL GENERATED RECOMMENDATION " + "="*20))
        self.stdout.write(recommendation)
        self.stdout.write("="*71 + "\n")

        #  Save to Database 
        latest_report.recommendation = recommendation
        latest_report.save()
        self.stdout.write(self.style.SUCCESS(f"✅ Recommendation saved to database for report ID: {latest_report.id}."))

    def initialize_vector_store(self, knowledge_base_file_path, chroma_path):
        if os.path.exists(chroma_path):
            shutil.rmtree(chroma_path)
        
        if not os.path.exists(knowledge_base_file_path):
            self.stdout.write(self.style.ERROR(f"Knowledge base file not found at '{knowledge_base_file_path}'."))
            return None
        
        loader = TextLoader(knowledge_base_file_path, encoding='utf-8')
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-MiniLM-L6-v2", model_kwargs={'device': 'cpu'})
        
        vectorstore = Chroma.from_documents(documents=chunks, embedding=embedding_function, persist_directory=chroma_path)
        self.stdout.write("Vector store initialized successfully.")
        return vectorstore

    def format_kpi_text(self, report):
        top_dishes = sorted(report.dish_performance, key=lambda x: x.get('sold', 0), reverse=True)[:3]
        dish_summary = "\n".join([f"  - {d.get('dish_name', 'N/A')}: {d.get('sold', 0)} sold" for d in top_dishes])

        slow_hours_list = sorted(report.avg_hourly_orders, key=lambda item: item.get('orders', 0))[:3]
        slow_hour_summary = "\n".join([f"  - {item.get('hour', 'N/A')}:00: {item.get('orders', 0)} avg orders" for item in slow_hours_list])
        peak_hours_list = sorted(report.avg_hourly_orders, key=lambda item: item.get('orders', 0), reverse=True)[:3]
        peak_hour_summary = "\n".join([f"  - {item.get('hour', 'N/A')}:00: {item.get('orders', 0)} avg orders" for item in peak_hours_list])

        kpi_text = f"""
📅 Week: {report.start_date} to {report.end_date}
- Total Sales Revenue: ₱{report.total_sales_revenue}
- Total Order Count: {report.total_order_count}
- Online Orders: {report.online_order_count}
- Walk-in Orders: {report.walkin_order_count}
- Avg Items per Order: {report.avg_items_per_order}

🍽️ Top Performing Dishes:
{dish_summary}

⏰ Peak Order Hours:
{peak_hour_summary}

🕒 Slowest Hours of the Day:
{slow_hour_summary}
""".strip()
        
        kpi_raw = {
            "total_sales_revenue": report.total_sales_revenue,
            "online_order_count": report.online_order_count,
            "walkin_order_count": report.walkin_order_count,
            "avg_items_per_order": report.avg_items_per_order,
        }

        return kpi_text, kpi_raw, slow_hours_list

    def generate_kb_query_from_kpis(self, kpis_dict, slow_hours):
        query_parts = []
        if float(kpis_dict.get("total_sales_revenue", 0)) < 150000: 
            query_parts.append("strategies to increase overall restaurant sales revenue")
        if float(kpis_dict.get("avg_items_per_order", 0)) < 3.0:
            query_parts.append("how to increase average order size and upsell items")
        if len(slow_hours) >= 3 and any(h['orders'] < 1.0 for h in slow_hours):
             query_parts.append("how to attract customers during off-peak or slow hours")
        if not query_parts:
            return "general strategies to improve restaurant operations and menu performance"
        return ", ".join(query_parts)

    def generate_recommendation_from_llm(self, prompt: str):
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error calling Gemini API: {e}"))
            return None

    def build_system_prompt(self, kpi_text, last_week_reco, last_week_status_text, context, report):
        restaurant_info = """
RESTAURANT PROFILE:

LUK'S BY GOODCHOICE is a fast-casual Filipino diner located in a busy urban area with consistently high foot traffic. It has been in operation for approximately one and a half year.

Key Characteristics:
- Restaurant Type: Fast-casual, Filipino comfort food.
- Location: High-traffic commercial area.
- Operating Hours: Open 24 hours a day, from Monday to Saturday (closed on Sundays).
- Capacity: Can accommodate up to 120 dine-in customers at once.
- Ordering System:
  - Online kiosk accessible via customers' personal devices.
  - Orders placed online must still be paid for in-store.
  - Walk-in customers may also order directly at the counter.
"""
        
        system_prompt = f"""
{restaurant_info}

You are an expert restaurant business strategist. Your task is to act as a consultant, determine the key issues of the restaurant based on the sales data, and provide a single, comprehensive, actionable recommendation for the upcoming week. To do this, you must analyze various sources of information: general business principles, last week's recommendation, its corresponding status, and the current week's sales data. Your final recommendation must be a logical next step, building upon or diverging from last week's advice based on the new data. DO NOT simply repeat the previous recommendation.

CURRENT WEEK'S KPIs (Analytics Data for this Week):
{kpi_text}

PREVIOUS WEEK'S RECOMMENDATION (Last Week's Advice):
{last_week_reco or "N/A"}

PREVIOUS WEEK'S RECOMMENDATION STATUS:
{last_week_status_text}

CONTEXT FROM THE KNOWLEDGE BASE (General Strategies):
{context}

TASK:
Provide your observations for the week and identify potential issues. Review the general strategies, the PREVIOUS WEEK'S RECOMMENDATION, PREVIOUS WEEK'S RECOMMENDATION STATUS, and the CURRENT WEEK'S KPIs. Generate a new, follow-up strategy. What is the logical next step? Generate a unified strategic recommendation that considers the given factors.

STRICTLY FOLLOW THIS FORMAT: (
## Weekly Business Insights (Week of {report.start_date.strftime('%B %d, %Y')})

**Summary:** 
(Start with a brief summary of the current week's performance.)

**Observations & Potential Issues:** 
(List down the identified key issues or opportunities in a bulleted form with its corresponding description.)

**Recommendation for Next Week:** 
(Provide an actionable recommendation for the upcoming week, building on or diverging from last week's advice.)
)

**IMPORTANT:**
- Your recommendation should be a single, clear action item that the restaurant can implement next week.
- It should not be a repeat of last week's recommendation unless it is a necessary follow-up.
- DO NOT stray too far from the context provided. Your recommendation must be grounded in the current week's KPIs and the previous week's recommendation.
- DO NOT include the restaurant's limitations in the potential issues section. Focus on the data and the recommendation.
""".strip()
        
        return system_prompt