#!/usr/bin/env python3
"""
Development script to kill all running CustomRPCManager instances.
Useful when the app bugs out and the window/tray is not visible.
Cross-platform support (Linux, macOS, Windows).
"""

import os
import sys
import time
import signal
import psutil
from pathlib import Path


def find_customrpc_processes():
    """Find all CustomRPCManager processes."""
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline:
                cmdline_str = ' '.join(cmdline)
                # Check if it's a Python process running customrpc
                if 'python' in proc.info['name'].lower() and 'customrpcmanager' in cmdline_str:
                    processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return processes


def kill_processes(processes):
    """Kill processes gracefully, then forcefully if needed."""
    if not processes:
        print("✅ No CustomRPCManager processes found running.")
        return
    
    print(f"🎯 Found {len(processes)} process(es) to kill")
    
    for proc in processes:
        try:
            print(f"🔪 Killing process {proc.pid} ({' '.join(proc.cmdline())})...")
            
            # Try graceful termination first
            proc.terminate()
            
            # Wait up to 2 seconds for graceful shutdown
            try:
                proc.wait(timeout=2)
                print(f"  ✓ Process {proc.pid} terminated gracefully")
            except psutil.TimeoutExpired:
                print(f"⚠️  Process {proc.pid} didn't respond to SIGTERM, sending SIGKILL...")
                proc.kill()
                proc.wait(timeout=1)
                print(f"  ✓ Process {proc.pid} killed forcefully")
                
        except psutil.NoSuchProcess:
            print(f"  ✓ Process {proc.pid} already terminated")
        except psutil.AccessDenied:
            print(f"  ✗ Access denied to kill process {proc.pid}")
        except Exception as e:
            print(f"  ✗ Error killing process {proc.pid}: {e}")


def cleanup_lock_files():
    """Clean up lock and port files."""
    print("\n🧹 Cleaning up lock and port files...")
    
    # Determine config directory based on platform
    if sys.platform == 'win32':
        config_dir = Path(os.environ.get('APPDATA', '')) / 'customrpcmanager'
    else:
        config_dir = Path.home() / '.config' / 'customrpcmanager'
    
    if config_dir.exists():
        lock_file = config_dir / '.lock'
        port_file = config_dir / '.port'
        
        try:
            if lock_file.exists():
                lock_file.unlink()
                print("  ✓ Removed lock file")
        except Exception as e:
            print(f"  ✗ Failed to remove lock file: {e}")
        
        try:
            if port_file.exists():
                port_file.unlink()
                print("  ✓ Removed port file")
        except Exception as e:
            print(f"  ✗ Failed to remove port file: {e}")
    else:
        print("  ℹ Config directory not found, nothing to clean up")


def main():
    """Main function."""
    print("🔍 Searching for CustomRPCManager processes...")
    
    # Check lock and port files
    if sys.platform == 'win32':
        config_dir = Path(os.environ.get('APPDATA', '')) / 'customrpcmanager'
    else:
        config_dir = Path.home() / '.config' / 'customrpcmanager'
    
    lock_file = config_dir / '.lock'
    port_file = config_dir / '.port'
    
    if lock_file.exists():
        try:
            lock_pid = lock_file.read_text().strip()
            if lock_pid:
                print(f"📄 Lock file PID: {lock_pid}")
        except:
            pass
    
    if port_file.exists():
        try:
            port = port_file.read_text().strip()
            if port:
                print(f"📄 IPC Port: {port}")
        except:
            pass
    
    print()
    
    processes = find_customrpc_processes()
    
    if processes:
        print(f"\n📋 Found the following CustomRPCManager processes:")
        for proc in processes:
            try:
                print(f"  PID {proc.pid}: {' '.join(proc.cmdline())}")
            except:
                print(f"  PID {proc.pid}: <command line unavailable>")
        print()
    
    kill_processes(processes)
    
    # Verify all processes are killed
    time.sleep(1)
    print("\n🔍 Verifying all processes are killed...")
    remaining = find_customrpc_processes()
    
    if not remaining:
        print("✅ All CustomRPCManager processes have been terminated!")
    else:
        print(f"⚠️  {len(remaining)} process(es) may still be running:")
        for proc in remaining:
            try:
                print(f"  PID {proc.pid}: {' '.join(proc.cmdline())}")
            except:
                print(f"  PID {proc.pid}: <command line unavailable>")
    
    cleanup_lock_files()
    
    print("\n🎉 Done!")


if __name__ == '__main__':
    main()
