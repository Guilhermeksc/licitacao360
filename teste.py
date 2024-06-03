import contextily as ctx
print(ctx.providers.keys())  # Isso listará todos os provedores disponíveis
print(ctx.providers.Stamen.keys())  # Listar as variantes para o provedor Stamen, se existir
