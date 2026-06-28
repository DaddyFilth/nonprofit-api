"""
Donation marketing module using LLM APIs.

Generates marketing copy including thank you emails, social media posts,
and press releases when suppliers agree to donations.
"""

import asyncio
from typing import Dict, Any, Optional
from procurement_bot.config import settings


class LLMProvider:
    """Base class for LLM providers."""
    
    async def generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text using the LLM."""
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """LLM provider using OpenAI API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
    
    async def generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text using OpenAI API."""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a helpful marketing assistant for a nonprofit organization."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"OpenAI API error: {response.text}")
                return ""
                
        except Exception as e:
            print(f"Error generating text with OpenAI: {e}")
            return ""


class AnthropicProvider(LLMProvider):
    """LLM provider using Anthropic API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
    
    async def generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text using Anthropic API."""
        try:
            import requests
            
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": f"You are a helpful marketing assistant for a nonprofit organization. {prompt}"
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            else:
                print(f"Anthropic API error: {response.text}")
                return ""
                
        except Exception as e:
            print(f"Error generating text with Anthropic: {e}")
            return ""


class GeminiProvider(LLMProvider):
    """LLM provider using Google Gemini API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text using Gemini API."""
        try:
            import requests
            
            headers = {"Content-Type": "application/json"}
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"You are a helpful marketing assistant for a nonprofit organization. {prompt}"
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(
                f"{self.base_url}/models/gemini-pro:generateContent?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                print(f"Gemini API error: {response.text}")
                return ""
                
        except Exception as e:
            print(f"Error generating text with Gemini: {e}")
            return ""


class MarketingGenerator:
    """Marketing copy generator using LLM APIs."""
    
    def __init__(self):
        self.llm_provider = self._get_llm_provider()
    
    def _get_llm_provider(self) -> LLMProvider:
        """Initialize the configured LLM provider."""
        if settings.llm_provider == "openai" and settings.openai_api_key:
            return OpenAIProvider(settings.openai_api_key)
        elif settings.llm_provider == "anthropic" and settings.anthropic_api_key:
            return AnthropicProvider(settings.anthropic_api_key)
        elif settings.llm_provider == "gemini" and settings.gemini_api_key:
            return GeminiProvider(settings.gemini_api_key)
        else:
            print(f"Warning: LLM provider '{settings.llm_provider}' not configured. Using template-based generator.")
            return TemplateMarketingGenerator()
    
    async def generate_thank_you_email(
        self,
        supplier_name: str,
        contact_person: Optional[str] = None,
        donation_details: str = "",
        impact_description: str = ""
    ) -> str:
        """Generate a personalized thank you email with strict organization identity."""
        
        greeting = f"Dear {contact_person}" if contact_person else f"Dear {supplier_name} Team"
        
        prompt = f"""
Write a heartfelt thank you email to {supplier_name} for their material donation to {settings.organization_operating_names}.

Details:
- Greeting: {greeting}
- Donation details: {donation_details}
- Impact: {impact_description}
- Organization: {settings.organization_operating_names}, a {settings.organization_mission} based in {settings.organization_location}
- Mission: Providing essential exterior home repair, property restoration, and maintenance for elderly and low-income families at absolutely no cost

The email should:
1. Express sincere gratitude for their material donation
2. Highlight the emotional impact - how their donation helps elderly residents stay safe and allows low-income families to remain in their homes
3. Mention that their contribution serves as a tax write-off under IRS Section 170 guidelines
4. Confirm that tax documentation will be provided for their corporate giving records
5. Mention how their contribution will be recognized (website, social media)
6. Be professional yet warm and emotionally resonant
7. Be approximately 200-300 words

Sign off as Michael Yessian from {settings.organization_operating_names}.
Include signature: Reply-to: {settings.reply_to_email}, {settings.contact_phone} (Text communication only)
"""
        
        if isinstance(self.llm_provider, TemplateMarketingGenerator):
            return self.llm_provider.generate_thank_you_email(
                supplier_name, contact_person, donation_details, impact_description
            )
        
        return await self.llm_provider.generate_text(prompt, max_tokens=400)
    
    async def generate_social_media_post(
        self,
        supplier_name: str,
        donation_details: str = "",
        platform: str = "twitter"
    ) -> str:
        """Generate a social media shoutout post with correct organization identity."""
        
        platform_limits = {
            "twitter": 280,
            "linkedin": 1300,
            "facebook": 63206,
            "instagram": 2200
        }
        
        char_limit = platform_limits.get(platform, 280)
        
        prompt = f"""
Write a social media post for {platform} thanking {supplier_name} for their material donation to {settings.organization_operating_names}.

Details:
- Organization: {settings.organization_operating_names}, a {settings.organization_mission} based in {settings.organization_location}
- Mission: Providing essential exterior home repair, property restoration, and maintenance for elderly and low-income families at absolutely no cost
- Donation: {donation_details}
- Character limit: {char_limit}
- Platform: {platform}

The post should:
1. Be emotionally engaging and shareable
2. Include relevant hashtags about helping elderly, community support, and {settings.organization_location}
3. Tag the company (use @CompanyHandle)
4. Highlight the emotional impact - how donation helps elderly residents stay safe and low-income families remain in their homes
5. Include a call-to-action if appropriate
"""
        
        if isinstance(self.llm_provider, TemplateMarketingGenerator):
            return self.llm_provider.generate_social_media_post(
                supplier_name, donation_details, platform
            )
        
        return await self.llm_provider.generate_text(prompt, max_tokens=300)
    
    async def generate_press_release(
        self,
        supplier_name: str,
        donation_details: str = "",
        project_description: str = "",
        quotes: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate a press release about the donation with correct organization identity."""
        
        quotes_text = ""
        if quotes:
            for person, quote in quotes.items():
                quotes_text += f'\n"{quote}" - {person}\n'
        
        prompt = f"""
Write a professional press release about {supplier_name}'s material donation to {settings.organization_operating_names}.

Details:
- Supplier: {supplier_name}
- Organization: {settings.organization_operating_names}, a {settings.organization_mission} based in {settings.organization_location}
- Mission: Providing essential exterior home repair, property restoration, and maintenance for elderly and low-income families at absolutely no cost
- Donation: {donation_details}
- Project: {project_description}
- Quotes: {quotes_text}

The press release should:
1. Follow standard press release format (FOR IMMEDIATE RELEASE, dateline, ###)
2. Include a compelling headline about helping elderly and low-income families in {settings.organization_location}
3. Cover the who, what, when, where, why
4. Emphasize the emotional impact - how donation helps elderly residents stay safe and low-income families remain in their homes
5. Include boilerplate about {settings.organization_operating_names} and its mission
6. Be approximately 400-600 words
7. Include media contact: Michael Yessian, {settings.reply_to_email}, {settings.contact_phone} (Text communication only)
"""
        
        if isinstance(self.llm_provider, TemplateMarketingGenerator):
            return self.llm_provider.generate_press_release(
                supplier_name, donation_details, project_description, quotes
            )
        
        return await self.llm_provider.generate_text(prompt, max_tokens=800)
    
    async def generate_all_marketing_materials(
        self,
        supplier_name: str,
        contact_person: Optional[str] = None,
        donation_details: str = "",
        impact_description: str = "",
        project_description: str = ""
    ) -> Dict[str, str]:
        """Generate all marketing materials at once with correct organization identity."""
        
        # Default project description if not provided
        if not project_description:
            project_description = f"Community initiative in {settings.organization_location} providing essential exterior home repair, property restoration, and maintenance for elderly and low-income families at absolutely no cost"
        
        thank_you_email = await self.generate_thank_you_email(
            supplier_name, contact_person, donation_details, impact_description
        )
        
        social_post = await self.generate_social_media_post(
            supplier_name, donation_details, platform="twitter"
        )
        
        press_release = await self.generate_press_release(
            supplier_name, donation_details, project_description
        )
        
        return {
            "thank_you_email": thank_you_email,
            "social_media_post": social_post,
            "press_release": press_release
        }


class TemplateMarketingGenerator(LLMProvider):
    """Template-based marketing generator when no LLM API is configured."""
    
    async def generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text using templates."""
        return "Template-based generation: Please configure an LLM API key for AI-generated content."
    
    def generate_thank_you_email(
        self,
        supplier_name: str,
        contact_person: Optional[str] = None,
        donation_details: str = "",
        impact_description: str = ""
    ) -> str:
        """Generate a template-based thank you email with emotional impact messaging."""
        
        greeting = f"Dear {contact_person}" if contact_person else f"Dear {supplier_name} Team"
        
        return f"""
{greeting},

On behalf of {settings.organization_operating_names}, I want to express our deepest gratitude for your generous material donation to our mission of helping elderly and low-income families in {settings.organization_location}.

{donation_details}

Your contribution will have a profound impact on vulnerable neighbors in our community:
{impact_description}

Because of your generosity, elderly residents can remain safe in their homes, and low-income families can avoid displacement. You're not just donating materials - you're helping people stay safe, maintain their dignity, and remain in the homes they love.

Your donation also serves as a tax write-off under IRS Section 170 guidelines, and we will provide all necessary documentation and tax receipts for your corporate giving records.

We are proud to recognize {supplier_name} as a valued partner in our mission. Your support will be acknowledged on our website, social media channels, and in upcoming press materials.

Thank you for believing in our work and for making a tangible difference in the lives of {settings.organization_location} residents who need it most.

With sincere gratitude,

Michael Yessian
{settings.organization_operating_names}
Reply-to: {settings.reply_to_email}
{settings.contact_phone} (Text communication only)
""".strip()
    
    def generate_social_media_post(
        self,
        supplier_name: str,
        donation_details: str = "",
        platform: str = "twitter"
    ) -> str:
        """Generate a template-based social media post with emotional impact messaging."""
        
        org_handle = settings.organization_operating_names.replace(' ', '')
        location_handle = settings.organization_location.replace(' ', '').replace(',', '')
        
        if platform == "twitter":
            return f"""
Huge thanks to @{supplier_name.replace(' ', '')} for their generous material donation! 🎉❤️

{donation_details}

Your support helps elderly residents stay safe in their homes and allows low-income families to remain in their homes. Together we're making {settings.organization_location} a better place for everyone! #CommunitySupport #HelpElderly #LawtonOK #{org_handle}
""".strip()
        else:
            return f"""
We're thrilled to announce a generous material donation from {supplier_name}! 

{donation_details}

This contribution will help {settings.organization_operating_names} continue our mission of providing essential exterior home repairs for elderly and low-income families in {settings.organization_location}. Your generosity keeps vulnerable neighbors safe and helps families remain in the homes they love. Thank you for being an amazing partner!

#CommunitySupport #HelpElderly #LowIncomeHousing #LawtonOK #CommunityRestoration #{org_handle}
""".strip()
    
    def generate_press_release(
        self,
        supplier_name: str,
        donation_details: str = "",
        project_description: str = "",
        quotes: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate a template-based press release with emotional impact messaging."""
        
        quotes_text = ""
        if quotes:
            for person, quote in quotes.items():
                quotes_text += f'\n"{quote}" - {person}\n'
        else:
            quotes_text = f'\n"We are incredibly grateful for {supplier_name}\'s generosity. Their donation will help elderly residents stay safe in their homes and allow low-income families to remain in their homes instead of facing displacement." - Michael Yessian, {settings.organization_operating_names}\n'
        
        return f"""
FOR IMMEDIATE RELEASE

{supplier_name} Partners with {settings.organization_operating_names} to Help Elderly and Low-Income Families in {settings.organization_location}

{settings.organization_location} - [Date] - {settings.organization_operating_names}, a {settings.organization_mission}, is proud to announce a generous material donation from {supplier_name}, supporting ongoing exterior home repair projects for elderly and low-income families throughout {settings.organization_location}.

{donation_details}

{project_description}

{quotes_text}

This partnership demonstrates {supplier_name}'s commitment to corporate social responsibility and community development. The donated materials will directly support vulnerable residents in {settings.organization_location}, helping elderly residents remain safe in their homes and allowing low-income families to avoid displacement. Through exterior home repairs and property maintenance, the organization ensures that everyone in the community has access to safe, well-maintained housing regardless of their financial situation.

About {settings.organization_operating_names}:
{settings.organization_operating_names} is a community-driven initiative based in {settings.organization_location} dedicated to providing essential exterior home repair, property restoration, and maintenance for elderly and low-income families at absolutely no cost. The organization believes that everyone deserves to live in a safe, well-maintained home, regardless of their financial situation, and focuses on making tangible differences in the lives of vulnerable neighbors through material donations and volunteer restoration efforts.

Media Contact:
Michael Yessian
{settings.organization_operating_names}
Reply-to: {settings.reply_to_email}
{settings.contact_phone} (Text communication only)

###
""".strip()


# Singleton instance
marketing_generator = MarketingGenerator()