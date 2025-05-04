import json
from tabulate import tabulate
from collections import defaultdict


def process_k6_data(file_path):
    with open(file_path) as f:
        data = [json.loads(line) for line in f if line.strip()]

    scenarios = defaultdict(lambda: {
        'requests': [],
        'durations': [],
        'checks_passed': 0,
        'checks_total': 0,
        'data_sent': 0,
        'data_received': 0
    })

    current_vu = None
    current_scenario = None

    for entry in data:
        try:
            # Handle metric definitions first
            if entry.get('type') == 'Metric':
                continue  # Skip metric definitions

            metric_type = entry.get('metric')
            data_obj = entry.get('data', {})

            if metric_type == 'vus':
                current_vu = data_obj.get('value', 0)
            elif metric_type == 'http_reqs':
                scenarios[data_obj.get('tags', {}).get('scenario', 'default')]['requests'].append({
                    'timestamp': data_obj.get('time'),
                    'method': data_obj.get('tags', {}).get('method'),
                    'url': data_obj.get('tags', {}).get('url'),
                    'duration': None,
                    'status': data_obj.get('tags', {}).get('status')
                })
            elif metric_type == 'http_req_duration':
                current_scenario = data_obj.get('tags', {}).get('scenario', 'default')
                scenarios[current_scenario]['durations'].append(data_obj.get('value', 0))
            elif metric_type == 'checks':
                current_scenario = data_obj.get('tags', {}).get('scenario', 'default')
                scenarios[current_scenario]['checks_passed'] += data_obj.get('value', 0)
                scenarios[current_scenario]['checks_total'] += 1
            elif metric_type == 'data_sent':
                current_scenario = data_obj.get('tags', {}).get('scenario', 'default')
                scenarios[current_scenario]['data_sent'] += data_obj.get('value', 0)
            elif metric_type == 'data_received':
                current_scenario = data_obj.get('tags', {}).get('scenario', 'default')
                scenarios[current_scenario]['data_received'] += data_obj.get('value', 0)

        except KeyError as e:
            print(f"Skipping malformed entry: {e}")
            continue

    return scenarios


def generate_report(scenarios, vu_count):
    # Modified to include VU count and success rate in reporting
    report = []
    summary = []

    for scenario, data in scenarios.items():
        if data['durations']:
            avg_duration = sum(data['durations']) / len(data['durations'])
            min_duration = min(data['durations'])
            max_duration = max(data['durations'])
            p95 = sorted(data['durations'])[int(len(data['durations']) * 0.95)]
        else:
            avg_duration = min_duration = max_duration = p95 = 0

        success_rate = (
            len([r for r in data['requests'] if r['status'] == '200']) / len(data['requests']) * 100
            if data['requests'] else 0
        )

        scenario_table = [
            ["Virtual Users", vu_count],
            ["Scenario Name", scenario],
            ["Total Requests", len(data['requests'])],
            ["Success Rate", f"{success_rate:.2f}%"],
            ["Avg Duration (ms)", f"{avg_duration:.2f}"],
            ["Min Duration (ms)", f"{min_duration:.2f}"],
            ["Max Duration (ms)", f"{max_duration:.2f}"],
            ["95th Percentile (ms)", f"{p95:.2f}"],
            ["Checks Passed", f"{data['checks_passed']}/{data['checks_total']}"],
            ["Data Sent (KB)", f"{data['data_sent'] / 1024:.2f}"],
            ["Data Received (KB)", f"{data['data_received'] / 1024:.2f}"]
        ]

        report.append(tabulate(scenario_table, tablefmt="github"))
        summary.append([
            vu_count,
            scenario,
            len(data['requests']),
            f"{avg_duration:.2f}±{p95:.2f}ms",
            f"{data['checks_passed']}/{data['checks_total']}",
            f"{data['data_sent'] / 1024:.2f}",
            f"{data['data_received'] / 1024:.2f}",
            f"{success_rate:.2f}%"  # Add success rate to summary
        ])

    return "\n".join(report), summary


def generate_comparison_report(all_summaries):
    # Add "Success Rate" to the headers
    headers = ["VUs", "Scenario", "Requests", "Latency (avg±p95)", "Checks Passed", "Data Sent (KB)",
               "Data Received (KB)", "Success Rate"]
    return tabulate(all_summaries, headers, tablefmt="github")


if __name__ == "__main__":
    vu_levels = [50, 100, 200, 500]
    all_summaries = []

    for vu in vu_levels:
        input_file = f"folderName/k6-{vu}.json"
        output_file = f"folderName/report-{vu}.md"

        try:
            scenarios = process_k6_data(input_file)
            report, summary = generate_report(scenarios, vu)
            all_summaries.extend(summary)

            with open(output_file, "w") as f:
                f.write(f"# K6 Load Test Report - {vu} Virtual Users\n\n")
                f.write(report)

            print(f"Generated report for {vu} VUs: {output_file}")
        except FileNotFoundError:
            print(f"Warning: File {input_file} not found, skipping")
        except Exception as e:
            print(f"Error processing {input_file}: {str(e)}")

    # Generate comparison report
    with open("folderName/comparison-report.md", "w") as f:
        f.write("# K6 Load Test Comparison Report\n\n")
        f.write(generate_comparison_report(all_summaries))
