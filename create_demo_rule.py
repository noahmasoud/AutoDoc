#!/usr/bin/env python3
"""
Script to create a rule for demo_java.js and demo_go.go files
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from db.session import get_db
from db.models import Rule, Template
from sqlalchemy import select

def get_test_template(db: Session):
    """Get the test template."""
    # Try to find a template with 'test' in the name
    templates = db.execute(select(Template)).scalars().all()
    
    for template in templates:
        if 'test' in template.name.lower():
            return template
    
    # If no test template, return first one or None
    return templates[0] if templates else None

def get_default_space_key(db: Session):
    """Get space_key from existing rules or use default."""
    rules = db.execute(select(Rule)).scalars().all()
    if rules:
        return rules[0].space_key
    return "TEST"  # Default space key

def create_rule():
    """Create the rule for demo files."""
    db: Session = next(get_db())
    
    try:
        print("=" * 60)
        print("Creating Rule for demo_java.js and demo_go.go")
        print("=" * 60)
        
        # Get test template
        print("\n1. Finding test template...")
        template = get_test_template(db)
        if template:
            print(f"   ✓ Found template: {template.name} (ID: {template.id})")
            template_id = template.id
        else:
            print("   ⚠ No test template found, creating rule without template")
            template_id = None
        
        # Get space_key
        print("\n2. Getting space_key...")
        space_key = get_default_space_key(db)
        print(f"   ✓ Using space_key: {space_key}")
        
        # Create rule
        print("\n3. Creating rule...")
        rule_name = "Demo JavaScript and Go Files"
        # Use regex selector to match both files
        selector = "regex:^(demo_java\\.js|demo_go\\.go)$"
        page_id = "6881281"
        
        print(f"   Name: {rule_name}")
        print(f"   Selector: {selector}")
        print(f"   Space Key: {space_key}")
        print(f"   Page ID: {page_id}")
        print(f"   Template ID: {template_id}")
        
        # Check if rule already exists
        existing = db.execute(
            select(Rule).where(Rule.name == rule_name)
        ).scalar_one_or_none()
        
        if existing:
            print(f"\n⚠ Rule already exists with ID: {existing.id}")
            print("   Updating existing rule...")
            existing.selector = selector
            existing.space_key = space_key
            existing.page_id = page_id
            existing.template_id = template_id
            db.commit()
            db.refresh(existing)
            print(f"✓ Rule updated successfully!")
            print(f"   Rule ID: {existing.id}")
            return existing
        else:
            new_rule = Rule(
                name=rule_name,
                selector=selector,
                space_key=space_key,
                page_id=page_id,
                template_id=template_id,
                auto_approve=False,
                priority=0
            )
            db.add(new_rule)
            db.commit()
            db.refresh(new_rule)
            print(f"\n✓ Rule created successfully!")
            print(f"   Rule ID: {new_rule.id}")
            return new_rule
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    rule = create_rule()
    sys.exit(0 if rule else 1)
