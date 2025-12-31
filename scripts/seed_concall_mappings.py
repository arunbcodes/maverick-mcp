#!/usr/bin/env python3
"""
Seed Conference Call IR Mappings.

This script populates the database with company IR mapping data from JSON seed files.
Supports bulk import, updates, and verification.

Usage:
    python scripts/seed_concall_mappings.py                    # Seed from default file
    python scripts/seed_concall_mappings.py --file custom.json # Seed from custom file
    python scripts/seed_concall_mappings.py --update           # Update existing mappings
    python scripts/seed_concall_mappings.py --verify           # Verify seeded data
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from maverick_data.models import CompanyIRMapping
from maverick_data import get_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ConcallMappingSeeder:
    """
    Seed company IR mappings into database.

    Handles bulk import, updates, and verification of IR mapping data.
    """

    def __init__(self, session):
        """
        Initialize seeder.

        Args:
            session: Database session
        """
        self.session = session

    def seed_from_json(
        self, json_file: Path, update_existing: bool = False
    ) -> dict[str, int]:
        """
        Seed mappings from JSON file.

        Args:
            json_file: Path to JSON file
            update_existing: Whether to update existing mappings

        Returns:
            dict: Statistics (added, updated, skipped)
        """
        logger.info(f"Loading mappings from {json_file}")

        try:
            with open(json_file) as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {json_file}")
            return {"added": 0, "updated": 0, "skipped": 0, "errors": 1}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_file}: {e}")
            return {"added": 0, "updated": 0, "skipped": 0, "errors": 1}

        companies = data.get("companies", [])
        if not companies:
            logger.warning("No companies found in JSON file")
            return {"added": 0, "updated": 0, "skipped": 0, "errors": 0}

        stats = {"added": 0, "updated": 0, "skipped": 0, "errors": 0}

        for company in companies:
            try:
                result = self._seed_company(company, update_existing)
                stats[result] += 1
            except Exception as e:
                logger.error(f"Failed to seed {company.get('ticker', 'UNKNOWN')}: {e}")
                stats["errors"] += 1

        # Commit all changes
        self.session.commit()
        logger.info(
            f"Seeding complete: {stats['added']} added, {stats['updated']} updated, "
            f"{stats['skipped']} skipped, {stats['errors']} errors"
        )

        return stats

    def _seed_company(self, company_data: dict[str, Any], update_existing: bool) -> str:
        """
        Seed single company mapping.

        Args:
            company_data: Company data dict
            update_existing: Whether to update if exists

        Returns:
            str: Operation performed (added, updated, skipped)
        """
        ticker = company_data["ticker"]

        # Check if exists
        existing = (
            self.session.query(CompanyIRMapping)
            .filter(CompanyIRMapping.ticker == ticker)
            .first()
        )

        if existing:
            if update_existing:
                # Update existing mapping
                self._update_mapping(existing, company_data)
                logger.info(f"Updated mapping for {ticker}")
                return "updated"
            else:
                logger.debug(f"Skipping existing mapping for {ticker}")
                return "skipped"
        else:
            # Create new mapping
            mapping = self._create_mapping(company_data)
            self.session.add(mapping)
            logger.info(f"Added new mapping for {ticker}")
            return "added"

    def _create_mapping(self, company_data: dict[str, Any]) -> CompanyIRMapping:
        """
        Create CompanyIRMapping from data dict.

        Args:
            company_data: Company data dict

        Returns:
            CompanyIRMapping: New mapping object
        """
        return CompanyIRMapping(
            ticker=company_data["ticker"],
            company_name=company_data["company_name"],
            ir_base_url=company_data.get("ir_base_url"),
            concall_url_pattern=company_data.get("concall_url_pattern"),
            concall_section_xpath=company_data.get("concall_section_xpath"),
            concall_section_css=company_data.get("concall_section_css"),
            market=company_data.get("market"),
            country=company_data.get("country"),
            is_active=company_data.get("is_active", True),
            notes=company_data.get("notes"),
        )

    def _update_mapping(
        self, mapping: CompanyIRMapping, company_data: dict[str, Any]
    ) -> None:
        """
        Update existing mapping with new data.

        Args:
            mapping: Existing mapping
            company_data: New company data
        """
        mapping.company_name = company_data["company_name"]
        mapping.ir_base_url = company_data.get("ir_base_url")
        mapping.concall_url_pattern = company_data.get("concall_url_pattern")
        mapping.concall_section_xpath = company_data.get("concall_section_xpath")
        mapping.concall_section_css = company_data.get("concall_section_css")
        mapping.market = company_data.get("market")
        mapping.country = company_data.get("country")
        mapping.is_active = company_data.get("is_active", True)
        mapping.notes = company_data.get("notes")

    def verify_seeded_data(self) -> dict[str, Any]:
        """
        Verify seeded data in database.

        Returns:
            dict: Verification statistics
        """
        logger.info("Verifying seeded data...")

        total = self.session.query(CompanyIRMapping).count()
        active = (
            self.session.query(CompanyIRMapping)
            .filter(CompanyIRMapping.is_active == True)
            .count()
        )
        inactive = total - active

        # Count by market
        markets = {}
        for market in ["NSE", "BSE", "NASDAQ", "NYSE"]:
            count = (
                self.session.query(CompanyIRMapping)
                .filter(CompanyIRMapping.market == market)
                .count()
            )
            if count > 0:
                markets[market] = count

        # Count by country
        countries = {}
        for country in ["IN", "US"]:
            count = (
                self.session.query(CompanyIRMapping)
                .filter(CompanyIRMapping.country == country)
                .count()
            )
            if count > 0:
                countries[country] = count

        stats = {
            "total": total,
            "active": active,
            "inactive": inactive,
            "by_market": markets,
            "by_country": countries,
        }

        logger.info(f"Verification complete:")
        logger.info(f"  Total mappings: {total}")
        logger.info(f"  Active: {active}, Inactive: {inactive}")
        logger.info(f"  By market: {markets}")
        logger.info(f"  By country: {countries}")

        return stats

    def list_mappings(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        List seeded mappings.

        Args:
            limit: Maximum number to list

        Returns:
            list: Mapping dicts
        """
        mappings = (
            self.session.query(CompanyIRMapping)
            .order_by(CompanyIRMapping.ticker)
            .limit(limit)
            .all()
        )

        results = []
        for mapping in mappings:
            results.append({
                "ticker": mapping.ticker,
                "company_name": mapping.company_name,
                "market": mapping.market,
                "country": mapping.country,
                "is_active": mapping.is_active,
                "has_url_pattern": bool(mapping.concall_url_pattern),
            })

        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Seed conference call IR mappings into database"
    )
    # Default to new package location, with fallback to legacy
    default_seed_file = (
        Path(__file__).parent.parent
        / "packages/india/src/maverick_india/concall/data/company_ir_seed.json"
    )
    # Fallback to legacy location if new doesn't exist
    if not default_seed_file.exists():
        default_seed_file = (
            Path(__file__).parent.parent
            / "packages/india/src/maverick_india/concall/data/company_ir_seed.json"
        )

    parser.add_argument(
        "--file",
        type=Path,
        default=default_seed_file,
        help="Path to JSON seed file",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing mappings (default: skip)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify seeded data after import",
    )
    parser.add_argument(
        "--list",
        type=int,
        metavar="N",
        help="List N seeded mappings",
    )

    args = parser.parse_args()

    # Get database session
    session = get_session()

    try:
        # Initialize seeder
        seeder = ConcallMappingSeeder(session)

        # Seed data
        if not args.list:
            stats = seeder.seed_from_json(args.file, update_existing=args.update)

            if stats["errors"] > 0:
                logger.error("Some mappings failed to seed. Check logs above.")
                return 1

        # Verify if requested
        if args.verify or not args.list:
            seeder.verify_seeded_data()

        # List if requested
        if args.list:
            mappings = seeder.list_mappings(args.list)
            print("\nSeeded Mappings:")
            print("-" * 80)
            for mapping in mappings:
                print(
                    f"{mapping['ticker']:15} {mapping['company_name']:40} "
                    f"{mapping['market']:6} {mapping['country']:3} "
                    f"{'✓' if mapping['is_active'] else '✗'}"
                )

        logger.info("Done!")
        return 0

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        return 1

    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
