#!/usr/bin/env python3
"""
Performance monitoring and report generation for Envy
"""
import psutil
import time
import sys
import logging
from pathlib import Path
from datetime import datetime
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PerfReport")


def get_gpu_info():
    """Get GPU information if available"""
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.used,memory.total,utilization.gpu', '--format=csv,noheader,nounits'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            gpus = []
            for line in lines:
                parts = line.split(', ')
                if len(parts) >= 4:
                    gpus.append({
                        'name': parts[0],
                        'memory_used': float(parts[1]),
                        'memory_total': float(parts[2]),
                        'utilization': float(parts[3])
                    })
            return gpus
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def monitor_system(duration=10, interval=1):
    """Monitor system for specified duration"""
    logger.info(f"Monitoring system for {duration} seconds...")
    
    measurements = {
        'cpu_percent': [],
        'memory_percent': [],
        'memory_used_mb': [],
        'gpu_utilization': [],
        'gpu_memory_used_mb': []
    }
    
    start_time = time.time()
    
    while time.time() - start_time < duration:
        # CPU and Memory
        measurements['cpu_percent'].append(psutil.cpu_percent(interval=0.1))
        mem = psutil.virtual_memory()
        measurements['memory_percent'].append(mem.percent)
        measurements['memory_used_mb'].append(mem.used / 1024 / 1024)
        
        # GPU (if available)
        gpus = get_gpu_info()
        if gpus:
            measurements['gpu_utilization'].append(gpus[0]['utilization'])
            measurements['gpu_memory_used_mb'].append(gpus[0]['memory_used'])
        
        time.sleep(interval)
    
    return measurements


def generate_report(measurements, output_path):
    """Generate performance report"""
    logger.info(f"Generating performance report: {output_path}")
    
    with open(output_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("ENVY PERSONAL ASSISTANT - PERFORMANCE REPORT\n")
        f.write("="*70 + "\n")
        f.write(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Duration: {len(measurements['cpu_percent'])} samples\n")
        f.write("\n")
        
        # System Info
        f.write("SYSTEM INFORMATION\n")
        f.write("-"*70 + "\n")
        f.write(f"CPU Cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical\n")
        mem = psutil.virtual_memory()
        f.write(f"Total Memory: {mem.total / 1024 / 1024 / 1024:.1f} GB\n")
        
        # GPU Info
        gpus = get_gpu_info()
        if gpus:
            f.write(f"GPU: {gpus[0]['name']}\n")
            f.write(f"GPU Memory: {gpus[0]['memory_total']:.0f} MB\n")
        else:
            f.write("GPU: Not detected or NVIDIA drivers not available\n")
        f.write("\n")
        
        # CPU Stats
        f.write("CPU USAGE\n")
        f.write("-"*70 + "\n")
        if measurements['cpu_percent']:
            f.write(f"Average: {sum(measurements['cpu_percent'])/len(measurements['cpu_percent']):.1f}%\n")
            f.write(f"Peak: {max(measurements['cpu_percent']):.1f}%\n")
            f.write(f"Minimum: {min(measurements['cpu_percent']):.1f}%\n")
        else:
            f.write("No data collected\n")
        f.write("\n")
        
        # Memory Stats
        f.write("MEMORY USAGE\n")
        f.write("-"*70 + "\n")
        if measurements['memory_used_mb']:
            f.write(f"Average: {sum(measurements['memory_used_mb'])/len(measurements['memory_used_mb']):.0f} MB ({sum(measurements['memory_percent'])/len(measurements['memory_percent']):.1f}%)\n")
            f.write(f"Peak: {max(measurements['memory_used_mb']):.0f} MB ({max(measurements['memory_percent']):.1f}%)\n")
            f.write(f"Minimum: {min(measurements['memory_used_mb']):.0f} MB ({min(measurements['memory_percent']):.1f}%)\n")
        else:
            f.write("No data collected\n")
        f.write("\n")
        
        # GPU Stats
        if measurements['gpu_utilization']:
            f.write("GPU USAGE\n")
            f.write("-"*70 + "\n")
            f.write(f"Average Utilization: {sum(measurements['gpu_utilization'])/len(measurements['gpu_utilization']):.1f}%\n")
            f.write(f"Peak Utilization: {max(measurements['gpu_utilization']):.1f}%\n")
            f.write(f"Average Memory: {sum(measurements['gpu_memory_used_mb'])/len(measurements['gpu_memory_used_mb']):.0f} MB\n")
            f.write(f"Peak Memory: {max(measurements['gpu_memory_used_mb']):.0f} MB\n")
            f.write("\n")
        
        # Recommendations
        f.write("RECOMMENDATIONS\n")
        f.write("-"*70 + "\n")
        
        avg_cpu = sum(measurements['cpu_percent'])/len(measurements['cpu_percent']) if measurements['cpu_percent'] else 0
        peak_cpu = max(measurements['cpu_percent']) if measurements['cpu_percent'] else 0
        avg_mem_pct = sum(measurements['memory_percent'])/len(measurements['memory_percent']) if measurements['memory_percent'] else 0
        
        if peak_cpu > 80:
            f.write("⚠ High CPU usage detected. Consider:\n")
            f.write("  - Using 'low' profile in config\n")
            f.write("  - Disabling local LLM and using remote fallback\n")
            f.write("  - Using smaller/quantized models\n")
        elif avg_cpu < 30:
            f.write("✓ CPU usage is healthy. You could:\n")
            f.write("  - Switch to 'power' profile for better performance\n")
            f.write("  - Enable larger models for better accuracy\n")
        else:
            f.write("✓ CPU usage is within normal range\n")
        
        f.write("\n")
        
        if avg_mem_pct > 80:
            f.write("⚠ High memory usage detected. Consider:\n")
            f.write("  - Closing other applications\n")
            f.write("  - Using smaller models\n")
            f.write("  - Reducing context length in config\n")
        elif avg_mem_pct < 50:
            f.write("✓ Memory usage is healthy\n")
        else:
            f.write("✓ Memory usage is within normal range\n")
        
        f.write("\n")
        f.write("="*70 + "\n")
    
    logger.info("Performance report generated successfully")


def main():
    """Main entry point"""
    output_path = Path(__file__).parent.parent / "artifacts" / "perf-report.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting performance monitoring...")
    logger.info("This will monitor system resources for 10 seconds")
    
    # Monitor
    measurements = monitor_system(duration=10, interval=1)
    
    # Generate report
    generate_report(measurements, output_path)
    
    logger.info(f"Report saved to: {output_path}")
    
    # Print summary
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    if measurements['cpu_percent']:
        print(f"CPU: {sum(measurements['cpu_percent'])/len(measurements['cpu_percent']):.1f}% avg, {max(measurements['cpu_percent']):.1f}% peak")
    if measurements['memory_used_mb']:
        print(f"Memory: {sum(measurements['memory_used_mb'])/len(measurements['memory_used_mb']):.0f} MB avg, {max(measurements['memory_used_mb']):.0f} MB peak")
    if measurements['gpu_utilization']:
        print(f"GPU: {sum(measurements['gpu_utilization'])/len(measurements['gpu_utilization']):.1f}% avg, {max(measurements['gpu_utilization']):.1f}% peak")
    print(f"\nFull report: {output_path}")
    print("="*70)


if __name__ == "__main__":
    main()
