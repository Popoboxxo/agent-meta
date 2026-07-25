import yaml

with open('config/role-defaults.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

for role_name, role_data in data.get('roles', {}).items():
    if 'description' in role_data and 'short_desc' not in role_data:
        desc = role_data['description']
        parts = desc.split('—')
        if len(parts) > 1:
            short = parts[0].strip()
        else:
            parts = desc.split(' - ')
            if len(parts) > 1:
                short = parts[0].strip()
            else:
                parts = desc.split('. ')
                short = parts[0].strip()
        if len(short) > 80:
            short = short[:77] + '...'
        role_data['short_desc'] = short

with open('config/role-defaults.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
