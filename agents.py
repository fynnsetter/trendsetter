import os
import requests
import json
from dotenv import load_dotenv
import anthropic

load_dotenv()
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

class TechnicalAgent:
    def __init__(self):
        if ANTHROPIC_API_KEY:
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        else:
            self.client = None
    
    def analyze(self, ticker, indicators):
        score = 0
        reasons = []
        
        current_price = indicators['current_price']
        ma_50 = indicators['ma_50']
        ma_200 = indicators['ma_200']
        rsi = indicators['rsi']
        macd_hist = indicators['macd_hist']
        volatility = indicators['volatility']
        
        if current_price > ma_50:
            score += 1
            reasons.append("Price above 50-day MA (+1)")
        else:
            score -= 1
            reasons.append("Price below 50-day MA (-1)")
        
        if current_price > ma_200:
            score += 1
            reasons.append("Price above 200-day MA (+1)")
        else:
            score -= 1
            reasons.append("Price below 200-day MA (-1)")
        
        if rsi < 30:
            score += 2
            reasons.append(f"RSI oversold ({rsi:.1f}) (+2)")
        elif rsi > 70:
            score -= 2
            reasons.append(f"RSI overbought ({rsi:.1f}) (-2)")
        else:
            reasons.append(f"RSI neutral ({rsi:.1f})")
        
        if macd_hist > 0:
            score += 1
            reasons.append("MACD bullish (+1)")
        else:
            score -= 1
            reasons.append("MACD bearish (-1)")
        
        explanation = f"Technical analysis: Score {score:+d}. {', '.join(reasons[:3])}"
        
        if self.client and ANTHROPIC_API_KEY:
            try:
                prompt = f"""You are a technical analyst. For {ticker}:
- Current price: ${current_price:.2f}
- 50-day MA: ${ma_50:.2f}
- 200-day MA: ${ma_200:.2f}
- RSI: {rsi:.1f}
- MACD Histogram: {macd_hist:.3f}
- Volatility: {volatility*100:.1f}%
Score: {score:+d}
Write a brief explanation (2-3 sentences)."""
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=150,
                    messages=[{"role": "user", "content": prompt}]
                )
                explanation = response.content[0].text.strip()
            except Exception as e:
                explanation = f"Technical analysis: Score {score:+d}."
        
        return {
            'ticker': ticker,
            'score': score,
            'reasons': reasons,
            'explanation': explanation,
            'indicators': {
                'rsi': rsi,
                'ma_50': ma_50,
                'ma_200': ma_200,
                'macd_hist': macd_hist,
                'volatility': volatility,
                'current_price': current_price
            }
        }


class FundamentalAgent:
    def __init__(self):
        if ANTHROPIC_API_KEY:
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        else:
            self.client = None
    
    def analyze(self, ticker, info):
        score = 0
        reasons = []
        
        pe_ratio = info.get('trailingPE', None)
        eps = info.get('trailingEps', None)
        revenue_growth = info.get('revenueGrowth', None)
        profit_margin = info.get('profitMargins', None)
        market_cap = info.get('marketCap', None)
        
        if pe_ratio:
            if pe_ratio < 20:
                score += 1
                reasons.append(f"P/E of {pe_ratio:.1f} is reasonable (+1)")
            elif pe_ratio > 30:
                score -= 1
                reasons.append(f"P/E of {pe_ratio:.1f} is high (-1)")
            else:
                reasons.append(f"P/E of {pe_ratio:.1f} is fair")
        
        if revenue_growth:
            if revenue_growth > 0.15:
                score += 1
                reasons.append(f"Revenue growth {revenue_growth*100:.1f}% is strong (+1)")
            elif revenue_growth > 0:
                reasons.append(f"Revenue growth {revenue_growth*100:.1f}% is positive")
            else:
                score -= 1
                reasons.append(f"Revenue growth {revenue_growth*100:.1f}% is negative (-1)")
        
        if profit_margin:
            if profit_margin > 0.20:
                score += 1
                reasons.append(f"Profit margin {profit_margin*100:.1f}% is healthy (+1)")
            elif profit_margin > 0:
                reasons.append(f"Profit margin {profit_margin*100:.1f}% is positive")
            else:
                score -= 1
                reasons.append(f"Profit margin {profit_margin*100:.1f}% is negative (-1)")
        
        explanation = f"Fundamental analysis: Score {score:+d}. {', '.join(reasons[:3])}"
        
        if self.client and ANTHROPIC_API_KEY:
            try:
                prompt = f"""You are a fundamental analyst. For {ticker}:
- P/E: {pe_ratio if pe_ratio else 'N/A'}
- EPS: ${eps if eps else 'N/A'}
- Revenue Growth: {revenue_growth*100 if revenue_growth else 'N/A'}%
- Profit Margin: {profit_margin*100 if profit_margin else 'N/A'}%
- Market Cap: ${market_cap/1e9:.2f}B if market_cap else 'N/A'
Score: {score:+d}
Write a brief explanation (2-3 sentences)."""
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=150,
                    messages=[{"role": "user", "content": prompt}]
                )
                explanation = response.content[0].text.strip()
            except Exception as e:
                explanation = f"Fundamental analysis: Score {score:+d}."
        
        return {
            'ticker': ticker,
            'score': score,
            'reasons': reasons,
            'explanation': explanation,
            'fundamentals': {
                'pe_ratio': pe_ratio,
                'eps': eps,
                'revenue_growth': revenue_growth,
                'profit_margin': profit_margin,
                'market_cap': market_cap
            }
        }


class SentimentAgent:
    def __init__(self):
        if ANTHROPIC_API_KEY:
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        else:
            self.client = None
    
    def analyze(self, ticker):
        headlines = ["No news headlines available"]
        score = 0
        
        if NEWS_API_KEY:
            try:
                url = f'https://newsapi.org/v2/everything?q={ticker}&language=en&pageSize=5&sortBy=relevancy&apiKey={NEWS_API_KEY}'
                response = requests.get(url, timeout=10)
                data = response.json()
                if data.get('status') == 'ok' and data.get('articles'):
                    headlines = [article['title'] for article in data['articles'][:5] if article['title']]
            except Exception as e:
                print(f"News API error: {str(e)[:50]}")
        
        explanation = f"Sentiment analysis: {len(headlines)} headlines found."
        
        if self.client and ANTHROPIC_API_KEY and headlines:
            try:
                news_text = "\n".join(headlines)
                prompt = f"""You are a sentiment analyst. Analyze these {ticker} headlines:
{news_text}
Score the sentiment (-2 to +2) and give a brief explanation."""
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=150,
                    messages=[{"role": "user", "content": prompt}]
                )
                explanation = response.content[0].text.strip()
            except Exception as e:
                explanation = f"Sentiment analysis: Could not analyze."
        
        return {
            'ticker': ticker,
            'score': score,
            'headlines': headlines,
            'explanation': explanation
        }


class Orchestrator:
    def __init__(self):
        if ANTHROPIC_API_KEY:
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        else:
            self.client = None
    
    def analyze(self, ticker, technical_result, fundamental_result, sentiment_result):
        total_score = (
            technical_result['score'] +
            fundamental_result['score'] +
            sentiment_result['score']
        )
        
        if total_score >= 6:
            recommendation = "STRONG BUY"
            position_pct = 15
        elif total_score >= 3:
            recommendation = "BUY"
            position_pct = 10
        elif total_score >= 0:
            recommendation = "HOLD / WAIT"
            position_pct = 5
        elif total_score >= -3:
            recommendation = "SELL / REDUCE"
            position_pct = 0
        else:
            recommendation = "STRONG SELL"
            position_pct = 0
        
        confidence = min(95, max(60, 85 - abs(total_score)))
        summary = f"{recommendation} with {confidence:.0f}% confidence. Score: {total_score:+d}."
        
        if self.client and ANTHROPIC_API_KEY:
            try:
                prompt = f"""Combine these analyses for {ticker}:
Technical: {technical_result['explanation']}
Fundamental: {fundamental_result['explanation']}
Sentiment: {sentiment_result['explanation']}
Total Score: {total_score:+d}
Recommendation: {recommendation}
Write a concise summary (2-3 sentences)."""
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}]
                )
                summary = response.content[0].text.strip()
            except Exception as e:
                summary = f"{recommendation} with {confidence:.0f}% confidence."
        
        return {
            'ticker': ticker,
            'total_score': total_score,
            'recommendation': recommendation,
            'confidence': confidence,
            'position_pct': position_pct,
            'summary': summary,
            'agent_results': {
                'technical': technical_result,
                'fundamental': fundamental_result,
                'sentiment': sentiment_result
            }
        }
