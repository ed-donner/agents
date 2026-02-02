#!/usr/bin/env python
"""
Advanced Investment Crew - Main Entry Point
Multi-agent system for portfolio analysis using Modern Portfolio Theory
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path if running directly
if __name__ == "__main__":
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

from advanced_investment_crew.crew import AdvancedInvestmentCrew


def print_banner():
    """Print application banner"""
    print("=" * 80)
    print("🚀 ADVANCED ETF PORTFOLIO ANALYZER")
    print("=" * 80)
    print("Powered by CrewAI | Modern Portfolio Theory | Multi-Agent System")
    print("=" * 80)


def get_market_selection():
    """Get market type selection from user"""
    print("\n📊 SELECT MARKET TYPE:")
    print("1. 🌍 Global Markets (USD)")
    print("   - SPY, QQQ, VTI, VXUS, AGG")
    print("2. 🇹🇷 Türkiye Piyasası (TRY)")
    print("   - THYAO.IS, AKBNK.IS, EREGL.IS, SAHOL.IS, BIMAS.IS")
    
    while True:
        choice = input("\nEnter choice (1 or 2): ").strip()
        if choice == '1':
            return 'US', 4.5  # ✅ 'US' olarak kalacak
        elif choice == '2':
            return 'Turkey', 25.0  # ✅ 'Turkey' olarak kalacak
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")


def get_period_selection():
    """Get time period selection from user"""
    print("\n📅 SELECT TIME PERIOD:")
    print("1. 1 Year")
    print("2. 2 Years (Recommended)")
    print("3. 5 Years")
    print("4. Maximum Available")
    
    period_map = {
        '1': ('1y', 365),
        '2': ('2y', 730),
        '3': ('5y', 1825),
        '4': ('max', 3650)
    }
    
    while True:
        choice = input("\nEnter choice (1-4): ").strip()
        if choice in period_map:
            return period_map[choice]
        else:
            print("❌ Invalid choice. Please enter 1-4.")


def calculate_dates(days):
    """Calculate start and end dates based on number of days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def run():
    """Run the crew with interactive user input"""
    try:
        print_banner()
        
        # Get user selections
        market_type, risk_free_rate = get_market_selection()
        
        # ✅ Kullanıcıya seçimini göster
        if market_type == 'Turkey':
            print(f"\n✅ Selected Market: TURKEY (Türkiye Piyasası)")
            print(f"📊 Tickers: THYAO.IS, AKBNK.IS, EREGL.IS, SAHOL.IS, BIMAS.IS")
        else:
            print(f"\n✅ Selected Market: US (Global Markets)")
            print(f"📊 Tickers: SPY, QQQ, VTI, VXUS, AGG")
        
        print(f"💰 Risk-Free Rate: {risk_free_rate}%")
        
        period, days = get_period_selection()
        print(f"✅ Selected Period: {period}")
        
        # Calculate dates
        start_date, end_date = calculate_dates(days)
        report_date = end_date.strftime('%Y%m%d')
        
        # ✅ Prepare inputs dictionary - market_type AYNEN gönderilecek
        inputs = {
            'market_type': market_type,  # 'US' veya 'Turkey'
            'period': period,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'risk_free_rate': risk_free_rate,
            'report_date': report_date
        }
        
        # ✅ Debug: Gönderilen değerleri göster
        print("\n" + "=" * 80)
        print("🔍 DEBUG: Inputs being sent to crew:")
        print("=" * 80)
        for key, value in inputs.items():
            print(f"   {key}: {value}")
        print("=" * 80)
        
        print("\n🔄 STARTING MULTI-AGENT ANALYSIS...")
        print("=" * 80)
        print("\nAgents will execute in sequence:")
        print("1. 📊 Market Data Researcher - Fetching & analyzing data")
        print("2. 🎯 Portfolio Optimizer - Calculating optimal allocations")
        print("3. ⚠️  Risk Analyst - Assessing portfolio risks")
        print("4. 📝 Report Writer - Generating investment report")
        print("\n" + "=" * 80 + "\n")
        
        # Create and run crew
        crew = AdvancedInvestmentCrew()
        result = crew.crew().kickoff(inputs=inputs)
        
        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE!")
        print("=" * 80)
        print(f"\n📄 Report saved to: reports/investment_report_{report_date}.md")
        print("\n💡 You can now:")
        print("   - Read the detailed report")
        print("   - Implement the recommended portfolio")
        print("   - Share with your financial advisor")
        print("\n⚠️  DISCLAIMER: This is for educational purposes only.")
        print("   Not financial advice. Consult a professional before investing.")
        print("\n" + "=" * 80)
        
        return result
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   - Check your internet connection")
        print("   - Verify API keys in .env file")
        print("   - Ensure all dependencies are installed")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_turkey():
    """Quick run for Turkish market (2 years)"""
    print_banner()
    print("\n🇹🇷 TURKISH MARKET ANALYSIS (2 Years)")
    print("=" * 80)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    inputs = {
        'market_type': 'Turkey',  # ✅ 'Turkey' olarak gönder
        'period': '2y',
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'risk_free_rate': 25.0,
        'report_date': end_date.strftime('%Y%m%d')
    }
    
    print("\n📊 Analysis Parameters:")
    for key, value in inputs.items():
        print(f"   {key}: {value}")
    print()
    
    try:
        crew = AdvancedInvestmentCrew()
        result = crew.crew().kickoff(inputs=inputs)
        
        print("\n✅ Turkish Market Analysis Complete!")
        print(f"📄 Report saved to: reports/investment_report_{inputs['report_date']}.md")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_us():
    """Quick run for US market (2 years)"""
    print_banner()
    print("\n🌍 US MARKET ANALYSIS (2 Years)")
    print("=" * 80)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    inputs = {
        'market_type': 'US',  # ✅ 'US' olarak gönder
        'period': '2y',
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'risk_free_rate': 4.5,
        'report_date': end_date.strftime('%Y%m%d')
    }
    
    print("\n📊 Analysis Parameters:")
    for key, value in inputs.items():
        print(f"   {key}: {value}")
    print()
    
    try:
        crew = AdvancedInvestmentCrew()
        result = crew.crew().kickoff(inputs=inputs)
        
        print("\n✅ US Market Analysis Complete!")
        print(f"📄 Report saved to: reports/investment_report_{inputs['report_date']}.md")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def train():
    """Train the crew for a given number of iterations"""
    try:
        print_banner()
        print("\n🎓 TRAINING MODE")
        print("=" * 80)
        
        n_iterations = int(input("Enter number of training iterations (default: 5): ").strip() or "5")
        filename = input("Enter training data filename (default: training_data.pkl): ").strip() or "training_data.pkl"
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        
        inputs = {
            'market_type': 'US',
            'period': '2y',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'risk_free_rate': 4.5,
            'report_date': end_date.strftime('%Y%m%d')
        }
        
        print(f"\n🔄 Training with {n_iterations} iterations...")
        print(f"💾 Will save to: {filename}\n")
        
        crew = AdvancedInvestmentCrew()
        crew.crew().train(
            n_iterations=n_iterations,
            filename=filename,
            inputs=inputs
        )
        
        print("\n✅ Training complete!")
        print(f"📄 Training data saved to: {filename}")
        
    except Exception as e:
        print(f"\n❌ Training error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def replay():
    """Replay the crew execution from a specific task"""
    try:
        print_banner()
        print("\n🔄 REPLAY MODE")
        print("=" * 80)
        
        task_id = input("Enter task ID to replay from: ").strip()
        
        if not task_id:
            print("❌ Task ID is required")
            sys.exit(1)
        
        print(f"\n🔄 Replaying from task: {task_id}\n")
        
        crew = AdvancedInvestmentCrew()
        crew.crew().replay(task_id=task_id)
        
        print("\n✅ Replay complete!")
        
    except Exception as e:
        print(f"\n❌ Replay error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test():
    """Test the crew execution with sample data"""
    try:
        print_banner()
        print("\n🧪 TEST MODE")
        print("=" * 80)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        inputs = {
            'market_type': 'US',
            'period': '1y',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'risk_free_rate': 4.5,
            'report_date': end_date.strftime('%Y%m%d')
        }
        
        print("\n📊 Test Parameters:")
        for key, value in inputs.items():
            print(f"   {key}: {value}")
        print("\n" + "=" * 80 + "\n")
        
        crew = AdvancedInvestmentCrew()
        result = crew.crew().test(
            n_iterations=1,
            openai_model_name='gpt-4o-mini',
            inputs=inputs
        )
        
        print("\n✅ Test complete!")
        return result
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'train':
            train()
        elif command == 'replay':
            replay()
        elif command == 'test':
            test()
        elif command == 'turkey':
            run_turkey()
        elif command == 'us':
            run_us()
        else:
            print(f"❌ Unknown command: {command}")
            print("\n📚 Available commands:")
            print("  python main.py              # Interactive mode (default)")
            print("  python main.py us           # Quick US market analysis")
            print("  python main.py turkey       # Quick Turkish market analysis")
            print("  python main.py test         # Quick test (1 year, gpt-4o-mini)")
            print("  python main.py train        # Train the crew")
            print("  python main.py replay       # Replay a specific task")
            sys.exit(1)
    else:
        run()
