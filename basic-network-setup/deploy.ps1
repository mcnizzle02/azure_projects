$env:LOCATION = "eastus"
$env:SUBSCRIPTION_ID = az account show --query id --output tsv

$env:RANDOM_SUFFIX = -join (1..6 | ForEach-Object { "{0:x}" -f (Get-Random -Maximum 16) })
$env:RESOURCE_GROUP = "rg-basic-network-$($env:RANDOM_SUFFIX)"
$env:VNET_NAME = "vnet-basic-network-$($env:RANDOM_SUFFIX)"
$env:VNET_ADDRESS_SPACE = "10.0.0.0/16"
$env:FRONTEND_SUBNET_NAME = "subnet-frontend"
$env:BACKEND_SUBNET_NAME = "subnet-backend"
$env:DATABASE_SUBNET_NAME = "subnet-database"

az group create `
    --name $env:RESOURCE_GROUP `
    --location $env:LOCATION `
    --tags purpose=recipe environment=demo tier=networking


az network vnet create `
    --resource-group $env:RESOURCE_GROUP `
    --name $env:VNET_NAME `
    --location $env:LOCATION `
    --address-prefixes $env:VNET_ADDRESS_SPACE `
    --subnet-name $env:FRONTEND_SUBNET_NAME `
    --subnet-prefixes "10.0.1.0/24" `
    --tags purpose=recipe environment=demo


 az network vnet subnet create `
    --resource-group $env:RESOURCE_GROUP `
    --vnet-name $env:VNET_NAME `
    --name $env:BACKEND_SUBNET_NAME `
    --address-prefixes "10.0.2.0/24"

az network vnet subnet create `
    --resource-group $env:RESOURCE_GROUP `
    --vnet-name $env:VNET_NAME `
    --name $env:DATABASE_SUBNET_NAME `
    --address-prefixes "10.0.3.0/24"


az network nsg create `
    --resource-group $env:RESOURCE_GROUP `
    --name "nsg-$($env:FRONTEND_SUBNET_NAME)" `
    --location $env:LOCATION `
    --tags purpose=recipe environment=demo tier=frontend

az network nsg rule create `
    --resource-group $env:RESOURCE_GROUP `
    --nsg-name "nsg-$($env:FRONTEND_SUBNET_NAME)" `
    --name "Allow-HTTP" `
    --protocol tcp `
    --priority 1000 `
    --destination-port-ranges 80 `
    --access allow `
    --direction inbound `
    --source-address-prefixes "*"