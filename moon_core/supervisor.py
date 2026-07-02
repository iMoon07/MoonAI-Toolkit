import asyncio
import signal
import sys
import os

class MoonSupervisor:
    def __init__(self):
        self.tasks = set()
        self.shutdown_hooks = []
        self.stop_flag = False

    def register(self, task: asyncio.Task):
        self.tasks.add(task)
        def _cleanup(_):
            self.tasks.discard(task)
        task.add_done_callback(_cleanup)

    def add_shutdown_hook(self, fn):
        """Register a sync or async function to run on shutdown."""
        self.shutdown_hooks.append(fn)

    async def shutdown(self):
        print("\n🔥 MoonSupervisor: Initiating staged shutdown...")
        self.stop_flag = True

        # Stage 1: Cancel active tasks
        print("   [Stage 1] Cancelling active tasks...")
        for t in list(self.tasks):
            t.cancel()

        # Stage 2: Run cleanup hooks with timeout protection
        print("   [Stage 2] Executing shutdown hooks...")
        for fn in self.shutdown_hooks:
            try:
                if asyncio.iscoroutinefunction(fn):
                    await asyncio.wait_for(fn(), timeout=3.0)
                else:
                    fn()
            except asyncio.TimeoutError:
                print(f"   [!] Hook {fn.__name__} timed out.")
            except Exception as e:
                print(f"   [!] Hook error: {e}")

        # Stage 3: Await task flush
        print("   [Stage 3] Waiting for tasks to flush...")
        if self.tasks:
            done, pending = await asyncio.wait(self.tasks, timeout=3.0)
            if pending:
                print(f"   [!] {len(pending)} tasks hanging.")
            else:
                print("   [Supervisor] All tasks acknowledged cancellation.")
        else:
            print("   [Supervisor] No active tasks to flush.")

        print("   [Supervisor] Hooks completed or timed out.")
        print("   [Stage 4] Shutdown pipeline complete. Entering final exit.")

    def install_signal(self):
        def handler(sig, frame):
            print("\n🧨 SIGINT received -> Triggering Graceful Shutdown")
            try:
                loop = asyncio.get_event_loop()
                
                def force_exit():
                    print("💀 Watchdog Timeout! Forcing os._exit(1)")
                    os._exit(1)
                    
                # Watchdog timer to ensure we never hang during shutdown
                if loop.is_running():
                    loop.call_later(10.0, force_exit)
                    future = asyncio.run_coroutine_threadsafe(self.shutdown(), loop)
                    future.add_done_callback(lambda _: os._exit(0))
                else:
                    loop.run_until_complete(self.shutdown())
                    os._exit(0)
            except Exception as e:
                print(f"Shutdown error: {e}")
                os._exit(1)

        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

# Global Supervisor
moon_supervisor = MoonSupervisor()
