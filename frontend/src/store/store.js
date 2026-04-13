import { configureStore, combineReducers } from '@reduxjs/toolkit';
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
// Импортируем напрямую из lib, чтобы избежать проблем с default
import storage from 'redux-persist/lib/storage';
import { apiSlice } from './apiSlice';

// Проверка на default, чтобы getItem точно нашелся
const actualStorage = storage.default ? storage.default : storage;

// ВАЖНО: Мы создаем rootReducer, чтобы persist работал корректно с RTK Query
const rootReducer = combineReducers({
   [apiSlice.reducerPath]: apiSlice.reducer,
});

const persistConfig = {
   key: 'root',
   storage: actualStorage, // Теперь здесь точно объект с getItem/setItem
   whitelist: [apiSlice.reducerPath],
   timeout: 1000,
   throttle: 500,
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
   reducer: persistedReducer,
   middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
         serializableCheck: {
            ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
         },
      }).concat(apiSlice.middleware),
});

setupListeners(store.dispatch);
export const persistor = persistStore(store);
