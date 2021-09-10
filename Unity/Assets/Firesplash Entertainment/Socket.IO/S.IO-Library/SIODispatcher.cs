using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using System;

namespace Firesplash.UnityAssets.SocketIO.Internal
{
	/// <summary>
	/// This behavior holds an action queue and dispatches those actions on the unity player's main thread. It's singleton is accessed through SIODispatcher.Instance
	/// </summary>
	internal class SIODispatcher : MonoBehaviour
	{
		private static SIODispatcher _instance = null;
		private static readonly Queue<Action> dispatchQueue = new Queue<Action>();
		int maxActionsPerFrame = 20;

		internal void Start()
		{
			StartCoroutine(DispatcherLoop());
		}

		IEnumerator DispatcherLoop()
		{
			int counter = 0;
			while (true)
			{
				counter = 0;
				lock (dispatchQueue)
				{
					while (dispatchQueue.Count > 0)
					{
						dispatchQueue.Dequeue().Invoke();
						if (counter++ >= maxActionsPerFrame)
						{
							counter = 0;
							yield return 0;
						}
					}
				}
				yield return 0;
			}
		}

		//Enqueues an Action to be run on the main thread
		internal void Enqueue(Action action)
		{
			lock (dispatchQueue)
			{
				dispatchQueue.Enqueue(action);
			}
		}

		internal static SIODispatcher Instance
		{
			get
			{
				return _instance;
			}
		}

		internal static void Verify()
		{
			if (_instance == null)
			{
				_instance = new GameObject("Firesplash.UnityAssets.SocketIO.SIODispatcher").AddComponent<SIODispatcher>();
				DontDestroyOnLoad(_instance.gameObject);
			}
		}

		void Awake()
		{
			if (_instance == null)
			{
				_instance = this;
				DontDestroyOnLoad(this.gameObject);
			}
		}

		void OnDestroy()
		{
			lock(dispatchQueue)
			{
				dispatchQueue.Clear();
			}
			_instance = null;
		}

		public static bool CheckAvailability()
		{
			if (SIODispatcher.Instance == null)
			{
				SocketIOManager.LogError("Unable to instantiate SIODispatcher. You can try to manually create a GameObject with the SIODispatcher Behaviour in your scene.");
				return false;
			}
			return true;
		}
	}
}