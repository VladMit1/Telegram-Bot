import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import {
   persistStore,
   persistReducer,
   FLUSH,
   REHYDRATE,
   PAUSE,
   PERSIST,
   PURGE,
   REGISTER,
} from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import { apiSlice } from './apiSlice';
const baseStorage = storage.default ? storage.default : storage;
const persistConfig = {
   key: 'root',
   storage: baseStorage,
   whitelist: [apiSlice.reducerPath], // Сохраняем только кэш запросов
};

const persistedReducer = persistReducer(persistConfig, apiSlice.reducer);

export const store = configureStore({
   reducer: {
      [apiSlice.reducerPath]: persistedReducer,
   },
   middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
         serializableCheck: {
            ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
         },
      }).concat(apiSlice.middleware),
});

setupListeners(store.dispatch);
export const persistor = persistStore(store);
