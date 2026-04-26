import random
from pathlib import Path
from logger import get_logger
import json
from datetime import datetime

class MetadataGenerator:
    """Advanced metadata generation with SEO optimization and viral hooks."""

    def __init__(self):
        self.logger = get_logger()

        # Viral hooks library
        self.viral_hooks = [
            "Wait for it... 😱",
            "You won't believe the ending! 🔥",
            "This changed everything 🤯",
            "Most satisfying thing you'll see today ✨",
            "I was not expecting that... 💀",
            "Level: IMPOSSIBLE 🏆",
            "Is this even real? 🧐",
            "Watch until the end! 👇",
            "Absolute perfection 💎",
            "Best Anime Moments 🌸",
            "Unbelievable Anime Art! ✨",
            "The details are insane... 🤯",
            "This Anime style is 10/10 🔥",
            "Wait for the transformation! 🎭",
            "Anime fans, you need to see this! 🇯🇵",
            "Satisfying Anime Vibes 🌙",
            "Legendary Anime Edit 💎",
            "Anime magic is real ✨",
            "POV: You found the best anime 🍿",
            "Can we talk about this animation? 🎨",
            "This edit goes HARD 🔥",
            "Hidden Gem Alert! 💎",
            "Top Tier Anime 🏆",
            "You need to watch this right now ‼️",
            "The 4K quality is insane! 💎",
            "Absolute 4K perfection ✨",
            "Best edit in Ultra HD 🏆",
            "Wait for the 4K drop! 🔥",
            "Top notch animation quality 💎",
            "When the animation hits different 😤",
            "This is peak content right here 📈",
            "No way this is real... 🤯",
            "The attention to detail is unreal ✨",
            "This deserves way more views 🔥",
            "Why isn't this viral yet? 🤔",
            "Animation at its finest 🎨",
            "This is what 4K was made for 💎",
            "The quality is actually insane 🤯",
            "Wait for the plot twist! 🌀",
            "This got me hooked instantly 🎣",
            "Can't stop watching this on repeat 🔁",
            "The vibes are immaculate ✨",
            "This is exactly what I needed today 💫",
            "Pure eye candy right here 👀",
            "The aesthetics are on point 🎯",
            "This is art in motion 🖼️",
            "When the quality matches the talent 🏆",
            "This deserves to go viral 🚀",
            "The edit game is strong 💪",
            "This is why I love anime ❤️",
            "The animation quality is next level 📈",
            "This is what perfection looks like 💎",
            "The attention to detail is crazy 🤯",
            "This is peak anime content 🗻",
            "The quality is unmatched 🏆",
            "This is what we call quality content ✨",
            "The animation is actually god-tier 🌟",
            "This deserves all the views 👀",
            "The edit quality is insane 🔥",
            "This is what viral content looks like 🚀"
        ]

        # SEO tags organized by category
        self.seo_tags = {
            "primary": [
                "Anime", "AnimeEdit", "AnimeShorts", "ViralAnime", "Otaku",
                "Manga", "AnimeArt", "Japan", "Animation", "AnimeLover"
            ],
            "secondary": [
                "Shorts", "Trending", "Viral", "Satisfying", "Amazing",
                "Edit", "Aesthetic", "ForYou", "FYP", "Explore"
            ],
            "quality": [
                "4K", "UltraHD", "HighQuality", "TopTier", "Premium",
                "Cinematic", "Professional", "Masterpiece", "Perfect", "Insane"
            ],
            "engagement": [
                "MustWatch", "WatchUntilEnd", "YouNeedToSeeThis", "BestContent",
                "HiddenGem", "Underrated", "Overlooked", "SleptOn", "ViralMaterial"
            ],
            "emotional": [
                "Satisfying", "Relaxing", "Exciting", "Amazing", "Beautiful",
                "Incredible", "Stunning", "MindBlowing", "Breathtaking", "Epic"
            ]
        }

        # Thumbnail concepts
        self.thumbnail_concepts = [
            "Split screen showing before/after transformation",
            "Close-up on most detailed element with dramatic lighting",
            "Character expression with emotional impact",
            "Action pose with dynamic motion blur",
            "Side-by-side comparison with quality difference",
            "Dramatic angle with depth of field",
            "Color-graded version with vibrant saturation",
            "Text overlay with hook phrase and emoji",
            "Character close-up with sparkles/effects",
            "Scene composition with rule of thirds",
            "Dramatic silhouette with backlighting",
            "Multiple characters in dynamic composition",
            "Detailed background art showcase",
            "Character design breakdown",
            "Animation technique highlight"
        ]

        # Description templates
        self.description_templates = [
            "This {content_type} is absolutely {adjective}! The {feature} is {quality} and you won't believe the {element}. Watch until the end for the {surprise}!",
            "POV: You just discovered the most {adjective} {content_type} ever. The {feature} alone is worth the {time_investment}. This is what {platform} is all about!",
            "When the {feature} hits different... 😤 This {content_type} has the most {quality} {element} I've ever seen. No wonder this is going {viral_status}!",
            "The {feature} in this {content_type} is actually {quality}. I've watched this {view_count} times and I still can't get over how {adjective} the {element} is!",
            "This is what {quality} {content_type} looks like. The {feature} is {adjective} and the {element} is {quality}. If you appreciate {appreciation_aspect}, you'll love this!",
            "Wait for the {surprise} at the end! This {content_type} has the most {adjective} {feature} and the {quality} is {quality_level}. This deserves to be {viral_status}!",
            "The attention to {detail_type} in this {content_type} is {quality}. Every {element} is {adjective} and the {feature} is {quality_level}. This is {appreciation_aspect} at its finest!",
            "I can't get over how {adjective} this {content_type} is. The {feature} is {quality} and the {element} is {quality_level}. This is why I love {platform}!"
        ]

        # SEO keywords
        self.seo_keywords = [
            "anime edit", "anime compilation", "best anime", "anime art",
            "anime animation", "anime moments", "anime scenes", "anime highlights",
            "anime shorts", "viral anime", "trending anime", "anime edits",
            "anime amv", "anime mmv", "anime edits 4k", "anime edits viral",
            "anime edits aesthetic", "anime edits satisfying", "anime edits amazing",
            "anime edits best", "anime edits top tier", "anime edits masterpiece",
            "anime edits god tier", "anime edits insane quality", "anime edits perfect"
        ]

    def generate_title(self, content_type="anime", caption=None, max_length=100):
        """
        Generate a high-CTR title with viral hooks.

        Args:
            content_type: Type of content ('anime', 'gaming', 'art', etc.)
            caption: Optional original caption to incorporate
            max_length: Maximum title length (YouTube limit is 100)

        Returns:
            Optimized title string
        """
        try:
            # Select random hook
            hook = random.choice(self.viral_hooks)

            # Build title components
            if caption and len(caption) > 10:
                # Incorporate caption if available
                caption_words = caption.split()[:3]  # Take first 3 words
                caption_snippet = " ".join(caption_words)
                title = f"{hook} {caption_snippet}"
            else:
                # Use content type
                content_nouns = {
                    "anime": "Anime Moments",
                    "gaming": "Gaming Highlights",
                    "art": "Digital Art",
                    "animation": "Animation Showcase"
                }
                noun = content_nouns.get(content_type, "Content")
                title = f"{hook} {noun}"

            # Ensure title length limit
            if len(title) > max_length:
                title = title[:max_length-3] + "..."

            self.logger.log_metadata_generated("title_generation", len(title), 0)
            return title

        except Exception as e:
            self.logger.log_processing_error("title_generation", "Title Generation", str(e))
            return "Amazing Content You Need to See! 🔥"

    def generate_description(self, title, content_type="anime", caption=None, include_cta=True):
        """
        Generate SEO-optimized description with tags and CTA.

        Args:
            title: Video title
            content_type: Type of content
            caption: Optional original caption
            include_cta: Whether to include call-to-action

        Returns:
            Optimized description string
        """
        try:
            # Select template
            template = random.choice(self.description_templates)

            # Fill template with random values
            adjectives = ["amazing", "incredible", "stunning", "breathtaking", "mind-blowing"]
            qualities = ["perfect", "flawless", "impeccable", "outstanding", "exceptional"]
            features = ["animation", "art style", "detail", "quality", "editing"]
            elements = ["character design", "background art", "color palette", "composition", "effects"]
            surprises = ["plot twist", "reveal", "transformation", "climax", "ending"]
            viral_statuses = ["viral", "trending", "famous", "popular", "legendary"]
            platforms = ["YouTube", "Shorts", "social media", "the internet", "content creation"]
            time_investments = ["30 seconds", "minute", "watch", "experience", "view"]
            detail_types = ["detail", "craft", "work", "effort", "precision"]
            appreciation_aspects = ["art", "animation", "creativity", "talent", "dedication"]
            quality_levels = ["next level", "god tier", "top tier", "unmatched", "unparalleled"]
            view_counts = ["10", "100", "1000", "countless", "endless"]

            description = template.format(
                content_type=content_type,
                adjective=random.choice(adjectives),
                feature=random.choice(features),
                quality=random.choice(qualities),
                element=random.choice(elements),
                surprise=random.choice(surprises),
                viral_status=random.choice(viral_statuses),
                platform=random.choice(platforms),
                time_investment=random.choice(time_investments),
                detail_type=random.choice(detail_types),
                appreciation_aspect=random.choice(appreciation_aspects),
                quality_level=random.choice(quality_levels),
                view_count=random.choice(view_counts)
            )

            # Add title at the beginning
            full_description = f"{title}\n\n{description}"

            # Add original caption if available
            if caption:
                full_description += f"\n\nOriginal: {caption}"

            # Add CTA
            if include_cta:
                ctas = [
                    "👍 Like if you enjoyed!",
                    "🔔 Subscribe for more amazing content!",
                    "💬 Comment your favorite part!",
                    "🔄 Share with friends who'd love this!",
                    "❤️ Follow for daily content!"
                ]
                full_description += f"\n\n{random.choice(ctas)}"

            # Add SEO tags
            tags = self.generate_tags(content_type)
            full_description += f"\n\n{tags}"

            self.logger.log_metadata_generated("description_generation", len(full_description), len(tags.split()))
            return full_description

        except Exception as e:
            self.logger.log_processing_error("description_generation", "Description Generation", str(e))
            return f"{title}\n\nAmazing content! Subscribe for more!"

    def generate_tags(self, content_type="anime", max_tags=15):
        """
        Generate optimized tags for SEO.

        Args:
            content_type: Type of content
            max_tags: Maximum number of tags

        Returns:
            Comma-separated tags string
        """
        try:
            # Select tags from different categories
            selected_tags = []

            # Always include primary tags
            selected_tags.extend(self.seo_tags["primary"][:5])

            # Add secondary tags
            selected_tags.extend(self.seo_tags["secondary"][:3])

            # Add quality tags
            selected_tags.extend(self.seo_tags["quality"][:2])

            # Add engagement tags
            selected_tags.extend(self.seo_tags["engagement"][:2])

            # Add emotional tags
            selected_tags.extend(self.seo_tags["emotional"][:2])

            # Add content-specific keywords
            content_keywords = [kw for kw in self.seo_keywords if content_type.lower() in kw.lower()]
            selected_tags.extend(content_keywords[:3])

            # Remove duplicates and limit
            unique_tags = list(dict.fromkeys(selected_tags))  # Preserve order, remove duplicates
            final_tags = unique_tags[:max_tags]

            tags_string = ",".join(final_tags)
            return tags_string

        except Exception as e:
            self.logger.log_processing_error("tag_generation", "Tag Generation", str(e))
            return "Anime,Shorts,Viral,Trending,ForYou"

    def generate_thumbnail_concept(self, content_type="anime"):
        """
        Generate a thumbnail concept description.

        Args:
            content_type: Type of content

        Returns:
            Thumbnail concept description
        """
        try:
            concept = random.choice(self.thumbnail_concepts)
            return f"Thumbnail Concept: {concept}"

        except Exception as e:
            self.logger.log_processing_error("thumbnail_generation", "Thumbnail Generation", str(e))
            return "Thumbnail Concept: Dramatic close-up with vibrant colors"

    def generate_complete_metadata(self, content_type="anime", caption=None, video_path=None):
        """
        Generate complete metadata package.

        Args:
            content_type: Type of content
            caption: Optional original caption
            video_path: Optional video path for analysis

        Returns:
            Dictionary with title, description, tags, thumbnail_concept
        """
        try:
            # Generate title
            title = self.generate_title(content_type, caption)

            # Generate description
            description = self.generate_description(title, content_type, caption)

            # Generate tags
            tags = self.generate_tags(content_type)

            # Generate thumbnail concept
            thumbnail_concept = self.generate_thumbnail_concept(content_type)

            metadata = {
                "title": title,
                "description": description,
                "tags": tags,
                "thumbnail_concept": thumbnail_concept,
                "generated_at": datetime.now().isoformat(),
                "content_type": content_type,
                "original_caption": caption if caption else ""
            }

            self.logger.log_metadata_generated(
                video_path if video_path else "metadata_generation",
                len(title),
                len(tags.split(","))
            )

            return metadata

        except Exception as e:
            self.logger.log_processing_error("metadata_generation", "Complete Metadata Generation", str(e))
            return {
                "title": "Amazing Content! 🔥",
                "description": "You need to see this! Subscribe for more!",
                "tags": "Viral,Trending,ForYou",
                "thumbnail_concept": "Dramatic close-up with vibrant colors"
            }

    def save_metadata(self, metadata, output_path):
        """
        Save metadata to JSON file.

        Args:
            metadata: Metadata dictionary
            output_path: Path to save metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            self.logger.log_processing_complete("metadata", "Metadata Save", output_path, 0)
            return True

        except Exception as e:
            self.logger.log_processing_error("metadata", "Metadata Save", str(e))
            return False

    def load_metadata(self, input_path):
        """
        Load metadata from JSON file.

        Args:
            input_path: Path to metadata file

        Returns:
            Metadata dictionary or None if failed
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            self.logger.log_processing_complete("metadata", "Metadata Load", input_path, 0)
            return metadata

        except Exception as e:
            self.logger.log_processing_error("metadata", "Metadata Load", str(e))
            return None